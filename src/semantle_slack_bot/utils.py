from numpy import dot
from numpy.linalg import norm


def cos_sim(vec1: list[float], vec2: list[float]) -> float:
    return float(dot(vec1, vec2) / (norm(vec1) * norm(vec2)))


def get_similarity(vec1: list[float], vec2: list[float]) -> float:
    return cos_sim(vec1, vec2) * 100
