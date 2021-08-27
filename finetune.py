from dotenv import load_dotenv

load_dotenv()

import openai

from datetime import datetime
import requests

POLL_INTERVAL_S = 30


if __name__ == "__main__":
    # upload the titles file
    upload_result = openai.File.create(
        file=open("titles.txt", "r"), purpose="fine-tune"
    )
    file_id = upload_result["id"]
    fine_tune = openai.FineTune.create(training_file=file_id, model="babbage")
    job_id = fine_tune["id"]

    fine_tuned_model_id = None
    while fine_tuned_model_id is None:
        try:
            events = openai.FineTune.stream_events(job_id)
            for event in events:
                print(
                    f'[{datetime.fromtimestamp(event["created_at"])}] {event["message"]}'
                )
        except requests.ConnectionError as e:
            # if there's a connection error, it probably just expired, the following code will retry
            # if the job is still running
            pass

        resp = openai.FineTune.retrieve(id=job_id)
        status = resp["status"]
        if status == "succeeded":
            fine_tuned_model_id = resp["fine_tuned_model"]
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
