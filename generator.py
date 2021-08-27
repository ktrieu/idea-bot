from dotenv import load_dotenv

load_dotenv()

from multiprocessing import Process
import os
import openai
import enum
import util

TEMPERATURE = 0.8
MAX_TOKENS = 64
STOP_SEQUENCE = "####"
N_ATTEMPTS = 5

PREFIX_TEXT = "Looking for a mathNEWS article idea? How about:"
MODEL_ID = os.environ.get("OPENAI_FINETUNED_MODEL")


class RequestType(enum.Enum):
    GENERATE = "generate"
    STOP = "stop"


class ResponseType(enum.Enum):
    GENERATE = "generate"


class GenerateRequest:
    def __init__(self, initial_text, channel_id, message_id):
        self.type = RequestType.GENERATE
        self.initial_text = initial_text
        self.channel_id = channel_id
        self.message_id = message_id


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

    def is_valid_completion(self, completion):
        if completion == "":
            return False
        # content filtering eventually goes here
        return True

    def generate_message(self, initial_text):
        if initial_text is None:
            self.logger.info(f"Generating prefixless message")
            return self.generate_completion(None)

        attempts = N_ATTEMPTS

        # Try N_ATTEMPTS times to generate a valid completion
        while attempts > 0:
            self.logger.info(
                f"Prefix message generation: attempt {N_ATTEMPTS - attempts + 1} of {N_ATTEMPTS}"
            )
            completion = self.generate_completion(initial_text)
            if self.is_valid_completion(completion):
                self.logger.info(f"Prefix message generation success")
                return initial_text + completion

            attempts -= 1

        # well, we tried
        self.logger.info(f"Attempts exhausted")
        return initial_text

    def generate_completion(self, initial_text):
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
        )
        return completion.choices[0].text

    def handle_request(self, request):
        if request.type == RequestType.GENERATE:
            self.logger.info(
                f"Generating with initial text: {request.initial_text} for {request.message_id}"
            )
            generated = self.generate_message(request.initial_text)
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
