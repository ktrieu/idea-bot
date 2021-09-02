from dotenv import load_dotenv

load_dotenv()

from multiprocessing import Process
import os
import openai
import enum
import util
from profanity_filter import ProfanityFilter

TEMPERATURE = 0.8
MAX_TOKENS = 64
STOP_SEQUENCE = "####"
N_ATTEMPTS = 5

MAX_INITIAL_TEXT_LEN = 128

CONTENT_FILTER_ENGINE = "content-filter-alpha-c4"
# False positive threshold for content filtering
TOXIC_THRESHOLD = -0.355
CONTENT_SAFE = "0"
CONTENT_SENSITIVE = "1"
CONTENT_HARMFUL = "2"

PREFIX_TEXT = "Looking for a mathNEWS article idea? How about:"
MODEL_ID = os.environ.get("OPENAI_FINETUNED_MODEL")

PROFANITY_FILTER = ProfanityFilter()


class RequestType(enum.Enum):
    GENERATE = "generate"
    STOP = "stop"


class ResponseType(enum.Enum):
    GENERATE = "generate"


class GenerateRequest:
    def __init__(self, initial_text, channel_id, message_id, user_id):
        self.type = RequestType.GENERATE
        self.initial_text = initial_text
        self.channel_id = channel_id
        self.message_id = message_id
        self.user_id = user_id


class StopRequest:
    def __init__(self):
        self.type = RequestType.STOP


class GenerateResponse:
    def __init__(self, generated, channel_id, message_id):
        self.type = ResponseType.GENERATE
        self.generated = generated
        self.channel_id = channel_id
        self.message_id = message_id


class GeneratorProcess(Process):
    def __init__(self, conn):
        Process.__init__(self)
        self.conn = conn
        self.sess = None
        self.terminate = False

    def start(self):
        Process.start(self)

    def is_harmful(self, completion, user_id):
        # https://beta.openai.com/docs/engines/content-filter
        response = openai.Completion.create(
            engine=CONTENT_FILTER_ENGINE,
            prompt="<|endoftext|>" + completion + "\n--\nLabel:",
            temperature=0,
            max_tokens=1,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            logprobs=10,
        )

        output_label = response.choices[0].text
        # If the classifier returns harmful, check probablity first
        # and reassign to the next most probable label if its below the threshold
        if output_label == CONTENT_HARMFUL:
            logprobs = response["choices"][0]["logprobs"]["top_logprobs"][0]

            if logprobs[CONTENT_HARMFUL] < TOXIC_THRESHOLD:
                prob_safe = logprobs.get(CONTENT_SAFE, None)
                prob_sensitive = logprobs.get(CONTENT_SENSITIVE, None)

                if prob_safe is not None and prob_sensitive is not None:
                    if prob_safe >= prob_sensitive:
                        output_label = CONTENT_SAFE
                    else:
                        output_label = CONTENT_SENSITIVE

                elif prob_safe is not None:
                    output_label = CONTENT_SAFE
                elif prob_sensitive is not None:
                    output_label = CONTENT_SENSITIVE

        if output_label not in [CONTENT_SAFE, CONTENT_SENSITIVE, CONTENT_HARMFUL]:
            output_label = CONTENT_HARMFUL

        return output_label == CONTENT_HARMFUL

    def is_profane(self, initial_text):
        return PROFANITY_FILTER.is_profane(initial_text)

    def is_valid_completion(self, completion):
        if completion == "":
            return False
        return True

    def generate_message(self, initial_text, user_id):
        if initial_text is None:
            self.logger.info(f"Generating prefixless message")
            return self.generate_completion(None, user_id)

        if len(initial_text) > MAX_INITIAL_TEXT_LEN:
            self.logger.info(
                f"Initial text was {len(initial_text)} characters long (maximum {MAX_INITIAL_TEXT_LEN})"
            )
            return "Your prompt was too long. Try again with a shorter one."

        attempts = N_ATTEMPTS

        # Try N_ATTEMPTS times to generate a valid completion
        while attempts > 0:
            self.logger.info(
                f"Prefix message generation: attempt {N_ATTEMPTS - attempts + 1} of {N_ATTEMPTS}"
            )
            completion = self.generate_completion(initial_text, user_id)
            if self.is_valid_completion(completion):
                self.logger.info(f"Prefix message generation success")
                return initial_text + completion

            attempts -= 1

        # well, we tried
        self.logger.info(f"Attempts exhausted")
        return initial_text

    def generate_completion(self, initial_text, user_id):
        if initial_text is not None:
            prompt = PREFIX_TEXT + " " + initial_text
        else:
            prompt = PREFIX_TEXT
        # The model performs worse with trailing spaces
        prompt = prompt.rstrip()
        completion = openai.Completion.create(
            model=MODEL_ID,
            prompt=prompt,
            max_tokens=MAX_TOKENS,
            stop=STOP_SEQUENCE,
            temperature=TEMPERATURE,
            user=str(user_id),
        )
        return completion.choices[0].text

    def handle_request(self, request):
        if request.type == RequestType.GENERATE:
            # reject prompts with profane input
            if request.initial_text is not None and self.is_profane(
                request.initial_text
            ):
                generated = (
                    "Sorry, your prompt contained profane language. Please try again."
                )
            else:
                self.logger.info(
                    f"Generating with initial text: {request.initial_text} for {request.message_id}"
                )
                generated = self.generate_message(request.initial_text, request.user_id)
                # do some censorship
                if self.is_harmful(generated, request.user_id):
                    generated = (
                        "Sorry, the response was determined to be harmful. Try again."
                    )

            self.conn.send(
                GenerateResponse(generated, request.channel_id, request.message_id)
            )
        elif request.type == RequestType.STOP:
            self.logger.info(f"Stop message received, terminating")
            self.terminate = True
        else:
            self.logger.error(f"Invalid message type received")

    def run(self):
        self.logger = util.create_logger(__name__)
        self.logger.info("Starting GeneratorProcess")

        try:
            while not self.terminate:
                request = self.conn.recv()
                self.handle_request(request)
        except KeyboardInterrupt:
            return
