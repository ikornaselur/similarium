import collections.abc

collections.Mapping = collections.abc.Mapping  # type: ignore

import json
import pickle
import re
from collections import namedtuple
from pathlib import Path

import gensim.models.keyedvectors as word2vec
from numpy import dot
from numpy.linalg import norm
from rich.console import Console
from rich.progress import MofNCompleteColumn, Progress, TimeElapsedColumn

ENGLISH_WORDS = Path(__file__).parent / "wordlists/english.txt"
BAD_WORDS = Path(__file__).parent / "wordlists/bad.txt"
TARGET_WORDS = Path(__file__).parent.parent / "src/semantle_slack_bot/target_words.json"

Word = namedtuple("Word", ["name", "vec", "norm"])
Similarities = list[tuple[float, str]]

console = Console()


def make_words(model: word2vec.KeyedVectors) -> dict[str, Word]:
    console.log("Loading english wordlist")
    with open(ENGLISH_WORDS, "r") as english_words_file:
        english_words = {line.strip() for line in english_words_file.readlines()}

    console.log("Loading bad word list")
    with open(BAD_WORDS, "r") as bad_words_file:
        bad_words = {line.strip() for line in bad_words_file.readlines()}

    wordlist = english_words - bad_words

    simple_word = re.compile("^[a-z]*$")
    words = {}
    for word in model.key_to_index:
        if simple_word.match(word) and word in wordlist:
            vec = model[word]
            words[word] = Word(name=word, vec=vec, norm=norm(vec))

    return words


def find_hints(words: dict[str, Word], secret: str) -> tuple[str, Similarities]:
    """Return hints for the 1,000 closest words"""
    target_word = words[secret]
    target_vec = target_word.vec
    target_vec_norm = target_word.norm

    similarities: Similarities = []

    for word in words.values():
        similarity = dot(word.vec, target_vec) / (word.norm * target_vec_norm)
        similarities.append((float(similarity), word.name))

    similarities.sort()

    # Closest items are at the end of the list, pick the last 1000
    nearest = similarities[-1000:]
    return secret, nearest


def main():
    vectors = str(Path(__file__).parent.parent / "GoogleNews-vectors-negative300.bin")
    console.log("Load vectors into model")
    model: word2vec.KeyedVectors = word2vec.KeyedVectors.load_word2vec_format(
        vectors, binary=True
    )

    words = make_words(model)

    console.log("Load target words")
    hints = {}
    with open(TARGET_WORDS, "r") as f:
        target_words = json.load(f)

    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        MofNCompleteColumn(),
    ) as progress:
        mapper = [
            find_hints(words, target)
            for target in progress.track(
                target_words, description="Finding hints for words..."
            )
        ]

    with open("hints.json", "w+") as hints_file:
        for secret, nearest in mapper:
            hints_file.write(json.dumps({"word": secret, "neighbors": nearest}))
            hints_file.write("\n")
            hints_file.flush()
            hints[secret] = nearest

    with open(b"nearest.pickle", "wb") as f:
        pickle.dump(hints, f)


if __name__ == "__main__":
    main()
