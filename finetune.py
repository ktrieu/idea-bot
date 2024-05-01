from dotenv import load_dotenv

load_dotenv()

from openai import OpenAI

client = OpenAI()

from datetime import datetime
import requests

POLL_INTERVAL_S = 30


if __name__ == "__main__":
    # upload the titles file
    upload_result = client.files.create(file=open("titles.txt", "r"), purpose="fine-tune")
    file_id = upload_result.id
    fine_tune = client.fine_tunes.create(training_file=file_id, model="babbage", n_epochs=2, prompt_loss_weight=1)
    job_id = fine_tune.id

    fine_tuned_model_id = None
    while fine_tuned_model_id is None:
        try:
            events = client.fine_tunes.stream_events(job_id)
            for event in events:
                print(
                    f'[{datetime.fromtimestamp(event.created_at)}] {event.message}'
                )
        except requests.ConnectionError as e:
            # if there's a connection error, it probably just expired, the following code will retry
            # if the job is still running
            pass

        resp = client.fine_tunes.retrieve(id=job_id)
        status = resp.status
        if status == "succeeded":
            fine_tuned_model_id = resp.fine_tuned_model
            print(f"Fine tune complete. Model id: {fine_tuned_model_id}")
        elif status == "running":
            # just retry
            pass
        elif status == "failed":
            print("Job failed. Oops.")
            exit(1)
        elif status == "cancelled":
            print("Job canceled. Presumably you did this on purpose.")
            exit(1)
