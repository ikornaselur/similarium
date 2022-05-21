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
class Logging:
    log_level: str
    web_log_level: str


@dc.dataclass
class Slack:
    dev_mode: bool
    bot_token: str
    app_token: str
    client_id: str
    client_secret: str
    signing_secret: str
    scopes: list[str]


@dc.dataclass
class Sentry:
    dsn: str
    env: str


@dc.dataclass
class Rules:
    similarity_count: int


@dc.dataclass
class Config:
    files: Files
    database: Database
    logging: Logging
    slack: Slack
    sentry: Sentry
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


_config_path = Path("./config.toml")
with open(_config_path, "r") as f:
    _config = toml.load(f)

config: Config = from_dict(Config, _config)
