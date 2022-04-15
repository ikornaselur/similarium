import sqlite3
from functools import partial
from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator

import gensim.models.keyedvectors as word2vec
import numpy as np
import numpy.typing as npt
from rich.console import Console
from rich.progress import MofNCompleteColumn, Progress, TimeElapsedColumn

DB_NAME = "word2vec.db"


def chunked(iterable: Iterable, n: int = 1000) -> Iterator:
    def take(n: int, iterable: Iterable) -> list:
        return list(islice(iterable, n))

    return iter(partial(take, n, iter(iterable)), [])


def bfloat(vec: npt.NDArray[np.float32]) -> bytes:
    """
    Half of each floating point vector happens to be zero in the Google model.
    Possibly using truncated float32 = bfloat. Discard to save space.
    """
    vec.dtype = np.int16  # type: ignore
    return vec[1::2].tobytes()


def main() -> None:
    console = Console()

    vectors = str(Path(__file__).parent.parent / "GoogleNews-vectors-negative300.bin")
    console.log("Load vectors into model")
    with console.status("Importing..."):
        model: word2vec.KeyedVectors = word2vec.KeyedVectors.load_word2vec_format(
            vectors, binary=True
        )

    console.log("Set up database")
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA journal_mode=WAL")
    cur = con.cursor()
    cur.execute("create table if not exists word2vec (word text PRIMARY KEY, vec blob)")
    con.commit()

    console.log("Delete existing data from database")
    with console.status("Deleting..."):
        con.execute("DELETE FROM word2vec")

    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        MofNCompleteColumn(),
    ) as progress:
        with con:
            words: list[str]
            for words in chunked(
                progress.track(
                    model.key_to_index,
                    description="Importing model to database...",
                )
            ):
                con.executemany(
                    "insert into word2vec values(?,?)",
                    ((word, bfloat(model[word])) for word in words),
                )
            console.log("Finishing up")


if __name__ == "__main__":
    main()
