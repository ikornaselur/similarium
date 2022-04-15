import sqlite3
import struct
from functools import lru_cache


def expand_bfloat(vec: bytes, half_length: int = 600) -> bytes:
    """
    expand truncated float32 to float32
    """
    if len(vec) == half_length:
        vec = b"".join((b"\00\00" + bytes(pair)) for pair in zip(vec[::2], vec[1::2]))
    return vec


@lru_cache(maxsize=50_000)
def get_model(secret: str, word: str) -> dict:
    con = sqlite3.connect("word2vec.db")
    cur = con.cursor()
    cur.execute(
        (
            "SELECT vec, percentile FROM word2vec left outer join nearby on "
            "nearby.word=? and nearby.neighbor=? WHERE word2vec.word = ?"
        ),
        (secret, word, word),
    )
    row = cur.fetchone()
    if row:
        row = list(row)
    con.close()
    if not row:
        return {}
    vec = row[0]
    result = {"vec": list(struct.unpack("300f", expand_bfloat(vec)))}
    if row[1]:
        result["percentile"] = row[1]
    return result
