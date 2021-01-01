from multiprocessing import Process
import logging
import gpt_2_simple as gpt2
import tensorflow as tf
import enum
import sys
import util

TEMPERATURE = 0.9
GENERATE_N_WORDS = 32
N_ATTEMPTS = 5
MAX_MESSAGES_BEFORE_RESET = 2


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

    def generate_message(self, initial_text):
        if initial_text is None:
            self.logger.info(f"Generating prefixless message")
            return self.generate_potential_message(None)

        attempts = N_ATTEMPTS

        # Try N_ATTEMPTS times to generate a message that isn't just the initial text
        while attempts > 0:
            self.logger.info(
                f"Prefix message generation: attempt {N_ATTEMPTS - attempts + 1} of {N_ATTEMPTS}"
            )
            potential_message = self.generate_potential_message(initial_text)
            if potential_message != initial_text:
                self.logger.info(f"Prefix message generation success")
                return potential_message

            attempts -= 1

        # well, we tried
        self.logger.info(f"Attempts exhausted")
        return potential_message

    def generate_potential_message(self, initial_text):
        with self.graph.as_default():
            generated = gpt2.generate(
                self.sess,
                length=GENERATE_N_WORDS,
                temperature=TEMPERATURE,
                truncate="\n\n",
                prefix=initial_text,
                return_as_list=True,
            )[0]
            self.messages_generated += 1
            return generated

    def reset_tf_session(self):
        if self.sess is None:
            self.sess = gpt2.start_tf_sess()
        else:
            self.sess = gpt2.reset_session(self.sess)
        gpt2.load_gpt2(self.sess)
        self.graph = tf.get_default_graph()
        self.messages_generated = 0

    def handle_request(self, request):
        if request.type == RequestType.GENERATE:
            self.logger.info(
                f"Generating with initial text: {request.initial_text} for {request.message_id}"
            )
            generated = self.generate_message(request.initial_text)
            self.conn.send(
                GenerateResponse(generated, request.channel_id, request.message_id)
            )
            self.reset_tf_session()
        elif request.type == RequestType.STOP:
            self.logger.info(f"Stop message received, terminating")
            self.terminate = True
        else:
            self.logger.error(f"Invalid message type received")

    def run(self):
        self.logger = util.create_logger(__name__)
        self.reset_tf_session()
        self.logger.info("Starting GeneratorProcess")

        try:
            while not self.terminate:
                request = self.conn.recv()
                self.handle_request(request)
        except KeyboardInterrupt:
            return
