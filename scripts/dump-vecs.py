import collections.abc
from functools import partial
from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator

collections.Mapping = collections.abc.Mapping  # type: ignore

import sqlite3

import gensim.models.keyedvectors as word2vec
import numpy as np
import numpy.typing as npt

from rich.progress import track
from rich.console import Console

DB_NAME = "word2vec.db"


def chunked(iterable: Iterable, n: int = 1000) -> Iterator:
    take = lambda n, iterable: list(islice(iterable, n))
    return iter(partial(take, n, iter(iterable)), [])


def bfloat(vec: npt.NDArray[np.float32]) -> bytes:
    """
    Half of each floating point vector happens to be zero in the Google model.
    Possibly using truncated float32 = bfloat. Discard to save space.
    """
    vec.dtype = np.int16  # type: ignore
    return vec[1::2].tobytes()


def main():
    console = Console()

    vectors = str(Path(__file__).parent.parent / "GoogleNews-vectors-negative300.bin")
    console.print("Load vectors into model")
    with console.status("Importing..."):
        model: word2vec.KeyedVectors = word2vec.KeyedVectors.load_word2vec_format(
            vectors, binary=True
        )

    console.print("Set up database")
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA journal_mode=WAL")
    cur = con.cursor()
    cur.execute("create table if not exists word2vec (word text PRIMARY KEY, vec blob)")
    con.commit()

    console.print("Delete existing data from database")
    with console.status("Deleting..."):
        con.execute("DELETE FROM word2vec")

    with con:
        words: list[str]
        for words in chunked(
            track(
                model.key_to_index,
                description="Importing model to database...",
            )
        ):
            con.executemany(
                "insert into word2vec values(?,?)",
                ((word, bfloat(model[word])) for word in words),
            )
        print("Finishing up")


if __name__ == "__main__":
    main()
