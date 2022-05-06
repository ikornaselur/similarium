import dataclasses as dc
from pathlib import Path
from typing import Any

import toml


class ConfigError(Exception):
    pass


class MissingKey(ConfigError):
    pass


@dc.dataclass
class Files:
    english: str
    bad_words: str
    vectors: str


@dc.dataclass
class Database:
    uri: str


@dc.dataclass
class Rules:
    similarity_count: int


@dc.dataclass
class Config:
    files: Files
    database: Database
    rules: Rules


def from_dict(klass, d) -> Any:
    if not dc.is_dataclass(klass):
        return d

    fieldtypes = {f.name: f.type for f in dc.fields(klass)}
    if missing := set(fieldtypes.keys()) - set(d.keys()):
        raise MissingKey(
            f"Missing key(s) in {klass.__name__} section: {', '.join(missing)}"
        )
    return klass(**{f: from_dict(fieldtypes[f], d[f]) for f in d})


_config_path = Path(__file__).parent.parent.parent / "config.toml"
with open(_config_path, "r") as f:
    _config = toml.load(f)

config: Config = from_dict(Config, _config)
