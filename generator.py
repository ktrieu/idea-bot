import pickle
import re
import os
import html
import itertools
import collections
import random

MARKOV_ORDER = 6

DUMP_LOCATION = "wordpress_dump.xml"
MODEL_LOCATION = "title_model.pickle"

START_MARKER = "SOL"
END_MARKER = "EOL"

# The next two functions are an implementation of a sliding window iterator,
# from: https://stackoverflow.com/questions/6822725/rolling-or-sliding-window-iterator
def consume(iterator, n):
    "Advance the iterator n-steps ahead. If n is none, consume entirely."
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(itertools.islice(iterator, n, n), None)


def window(iterable, n=2):
    "s -> (s0, ...,s(n-1)), (s1, ...,sn), (s2, ..., s(n+1)), ..."
    iters = itertools.tee(iterable, n)
    # Could use enumerate(islice(iters, 1, None), 1) to avoid consume(it, 0), but that's
    # slower for larger window sizes, while saving only small fixed "noop" cost
    for i, it in enumerate(iters):
        consume(it, i)
    return zip(*iters)


TITLE_REGEX = r"<title>(.+)</title>"


def extract_titles(dump_file):
    pattern = re.compile(TITLE_REGEX)
    matches = pattern.findall(dump_file.read())
    return [html.unescape(m) for m in matches]


def generate_model():
    titles = []
    try:
        with open(DUMP_LOCATION, "r", encoding="utf-8") as dump_file:
            titles = extract_titles(dump_file)
    except FileNotFoundError:
        print(f"No WordPress dump found at {DUMP_LOCATION}. Exiting.")
        exit()

    model_counts = collections.defaultdict(collections.Counter)

    for title in titles:
        # append start and end markers
        title_list = [START_MARKER] * MARKOV_ORDER + list(title) + [END_MARKER]
        for chars in window(title_list, n=MARKOV_ORDER + 1):
            key = chars[0:MARKOV_ORDER]
            value = chars[-1]
            counter = model_counts[tuple(key)]
            counter[value] += 1

    # process the raw counts into cumulative weights we can pass into random.choices later
    model_weights = dict()
    for k, counter in model_counts.items():
        total = 0
        chars = list()
        weights = list()
        for char, cnt in counter.items():
            total += cnt
            chars.append(char)
            weights.append(total)
        model_weights[k] = [chars, weights]

    # pickle the model and save it
    with open(MODEL_LOCATION, "wb") as model_file:
        pickle.dump(model_weights, model_file)

    return model_weights


def load_model():
    print("Loading model...")
    try:
        with open(MODEL_LOCATION, "rb") as model_file:
            print(f"Model loaded from {MODEL_LOCATION}.")
            return pickle.load(model_file)
    except FileNotFoundError:
        print("Model not found, regenerating from dump file...")
        return generate_model()


def generate(model, start=""):
    text = [START_MARKER] * MARKOV_ORDER
    for c in start:
        text.append(c)

    last = text[-MARKOV_ORDER:]

    while text[-1] != END_MARKER:
        try:
            chars, weights = model[tuple(last)]
        except KeyError:
            # we don't have this particular combination in our corpus
            return None
        text.append(random.choices(chars, cum_weights=weights)[0])
        last = text[-MARKOV_ORDER:]

    # remove the start and end markers
    text = text[MARKOV_ORDER:-1]

    return "".join(text)
