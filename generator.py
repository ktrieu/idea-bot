from multiprocessing import Process
import logging
import gpt_2_simple as gpt2
import tensorflow as tf
import enum

TEMPERATURE = 0.9
GENERATE_N_WORDS = 32
N_ATTEMPTS = 5
MAX_MESSAGES_BEFORE_RESET = 2


class RequestType(enum.Enum):
    GENERATE = "generate"
    STOP = "stop"


class GenerateRequest:
    def __init__(self, initial_text, message_id):
        self.type = RequestType.GENERATE
        self.initial_text = initial_text
        self.message_id = message_id


class StopRequest:
    def __init__(self):
        self.type = RequestType.STOP


class GeneratorProcess(Process):
    def __init__(self, conn):
        Process.__init__(self)
        self.conn = conn
        self.sess = None

    def start(self):
        Process.start(self)
        self.reset_tf_session()

    def generate_message(self, initial_text, message_id):
        if initial_text is None:
            logging.info(f"Generating prefixless message for {message_id}")
            return self.generate_potential_message(None)

        attempts = N_ATTEMPTS

        # Try N_ATTEMPTS times to generate a message that isn't just the initial text
        while attempts > 0:
            logging.info(
                f"Prefix message generation for {message_id}: attempt {N_ATTEMPTS - attempts + 1} of {N_ATTEMPTS}"
            )
            potential_message = self.generate_potential_message(initial_text)
            if potential_message != initial_text:
                logging.info(f"Prefix message generation success for {message_id}")
                return potential_message

            attempts -= 1

        # well, we tried
        logging.info(f"Attempts exhausted for {message_id}")
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

    def run(self):
        logging.info("Starting GeneratorProcess")

        while True:
            if self.conn.poll():
                msg = self.conn.recv()
                if msg.type == RequestType.GENERATE:
                    print(
                        f"Generating with initial text: {msg.initial_text} for {msg.message_id}"
                    )
                elif msg.type == RequestType.STOP:
                    print(f"Stop message received, terminating")
                    return
                else:
                    logging.error(f"Invalid message type received")
