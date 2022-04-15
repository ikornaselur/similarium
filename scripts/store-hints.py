import pickle
import sqlite3
from functools import partial
from itertools import islice
from typing import Iterable, Iterator

from rich.console import Console
from rich.progress import MofNCompleteColumn, Progress, TimeElapsedColumn

DB_NAME = "word2vec.db"


def chunked(iterable: Iterable, n: int = 1000) -> Iterator:
    def take(n: int, iterable: Iterable) -> list:
        return list(islice(iterable, n))

    return iter(partial(take, n, iter(iterable)), [])


def main() -> None:
    console = Console()

    console.log("Creating tables")
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA journal_mode=WAL")
    cur = con.cursor()
    cur.execute(
        """create table if not exists nearby
        (word text, neighbor text, similarity float, percentile integer,
        PRIMARY KEY (word, neighbor))"""
    )
    cur.execute(
        """create table if not exists similarity_range
        (word text PRIMARY KEY, top float, top10 float, rest float)"""
    )
    con.commit()

    console.log("Opening nearest pickle")
    with open(b"nearest.pickle", "rb") as f:
        nearest = pickle.load(f)

    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        MofNCompleteColumn(),
    ) as progress:
        with con:
            con.execute("DELETE FROM nearby")
            con.execute("DELETE FROM similarity_range")
            for secret, neighbors in progress.track(
                nearest.items(), description="Inserting hints to tables..."
            ):
                con.executemany(
                    (
                        "insert into nearby (word, neighbor, similarity, percentile) "
                        "values (?, ?, ?, ?)"
                    ),
                    (
                        (secret, neighbor, "%s" % score, (1 + idx))
                        for idx, (score, neighbor) in enumerate(neighbors)
                    ),
                )

                top = neighbors[-2][0]
                top10 = neighbors[-11][0]
                rest = neighbors[0][0]
                con.execute(
                    (
                        "insert into similarity_range (word, top, top10, rest) "
                        "values (?, ?, ?, ?)"
                    ),
                    (secret, "%s" % top, "%s" % top10, "%s" % rest),
                )

    con.commit()


if __name__ == "__main__":
    main()
