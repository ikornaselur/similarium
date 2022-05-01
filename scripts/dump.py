import asyncio
import heapq
import multiprocessing as mp
import re
from collections import namedtuple
from functools import partial
from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator

import gensim.models.keyedvectors as word2vec
import numpy as np
import numpy.typing as npt
from numpy import dot
from numpy.linalg import norm
from rich.console import Console
from rich.progress import MofNCompleteColumn, Progress, TimeElapsedColumn
from sqlalchemy.ext.asyncio.session import AsyncSession

from semantle_slack_bot import db
from semantle_slack_bot.config import config
from semantle_slack_bot.target_words import target_words

ROOT = Path(__file__).parent.parent

ENGLISH_WORDS = ROOT / config.files.english
BAD_WORDS = ROOT / config.files.bad_words
VECTORS_PATH = ROOT / config.files.vectors

Word = namedtuple("Word", ["name", "vec", "norm"])
Similarities = list[tuple[float, str]]

PROCESSES = max(mp.cpu_count() // 2, 1)
CHUNK_SIZE = 100

console = Console()


def chunked(iterable: Iterable, n: int = 10_000) -> Iterator:
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


def get_vectors() -> word2vec.KeyedVectors:
    console.log("Load vectors into model")
    with console.status("Importing..."):
        vectors: word2vec.KeyedVectors = word2vec.KeyedVectors.load_word2vec_format(
            VECTORS_PATH, binary=True
        )

    return vectors


def make_words(vectors: word2vec.KeyedVectors) -> dict[str, Word]:
    console.log("Loading english wordlist")
    with open(ENGLISH_WORDS, "r") as english_words_file:
        english_words = {line.strip() for line in english_words_file.readlines()}

    console.log("Loading bad word list")
    with open(BAD_WORDS, "r") as bad_words_file:
        bad_words = {line.strip() for line in bad_words_file.readlines()}

    wordlist = english_words - bad_words

    simple_word = re.compile("^[a-z]*$")
    words = {}
    for word in vectors.key_to_index:
        if simple_word.match(word) and word in wordlist:
            vec = vectors[word]
            words[word] = Word(name=word, vec=vec, norm=norm(vec))

    return words


def find_hints(
    words: list[Word],
    target: Word,
) -> tuple[str, Similarities]:
    """Return hints for the top closest words (from config)"""
    target_vec = target.vec
    target_vec_norm = target.norm

    similarities: Similarities = []

    for word in words:
        similarity = float(dot(word.vec, target_vec) / (word.norm * target_vec_norm))
        if len(similarities) < config.rules.similarity_count:
            heapq.heappush(similarities, (similarity, word.name))
        elif similarity > similarities[0][0]:
            heapq.heappushpop(similarities, (similarity, word.name))

    return (target.name, list(sorted(similarities)))


async def store_hints(nearest: dict[str, Similarities]) -> None:
    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        MofNCompleteColumn(),
    ) as progress:
        s: AsyncSession
        async with db.session() as s:
            await s.execute("PRAGMA journal_mode=WAL")

            for secret, neighbors in progress.track(
                nearest.items(), description="Inserting hints to tables..."
            ):
                await s.execute(
                    db.Nearby.__table__.insert(),
                    [
                        {
                            "word": secret,
                            "neighbor": neighbor,
                            "similarity": score,
                            "percentile": idx + 1,
                        }
                        for idx, (score, neighbor) in enumerate(neighbors)
                    ],
                )

                await s.execute(
                    db.SimilarityRange.__table__.insert(),
                    {
                        "word": secret,
                        "top": neighbors[-2][0],
                        "top10": neighbors[-11][0],
                        "rest": neighbors[0][0],
                    },
                )
                await s.flush()
            await s.commit()


async def dump_vecs(vectors: word2vec.KeyedVectors) -> None:
    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        MofNCompleteColumn(),
    ) as progress:
        s: AsyncSession
        async with db.session() as s:
            await s.execute("PRAGMA journal_mode=WAL")
            words: list[str]
            for words in chunked(
                progress.track(
                    vectors.key_to_index,
                    description="Importing model to database...",
                )
            ):
                await s.execute(
                    db.Word2Vec.__table__.insert(),
                    [{"word": word, "vec": bfloat(vectors[word])} for word in words],
                )
                await s.flush()
            await s.commit()


async def dump_hints(vectors: word2vec.KeyedVectors) -> None:
    words = make_words(vectors)

    console.log(f"Initialising multiprocessing pool with {PROCESSES} processes")
    pool = mp.Pool(processes=PROCESSES)
    words_values = list(words.values())

    hints: dict[str, Similarities] = {}

    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        MofNCompleteColumn(),
    ) as progress:
        task = progress.add_task(
            description="Finding hints for words...",
            total=len(target_words),
        )
        for word, nearest in pool.imap_unordered(
            partial(find_hints, words_values),
            (words[t] for t in target_words),
            chunksize=CHUNK_SIZE,
        ):
            hints[word] = nearest
            progress.advance(task, 1)

    await store_hints(hints)


async def main():
    vectors = get_vectors()
    await dump_vecs(vectors)
    await dump_hints(vectors)


if __name__ == "__main__":
    asyncio.run(main())
