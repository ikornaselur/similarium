import dataclasses as dc
import json
import os
from pathlib import Path
from typing import Any, ClassVar, Protocol, TypeVar, cast, overload

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
class SlackServer:
    port: int
    host: str
    path: str


@dc.dataclass
class Slack:
    dev_mode: bool
    bot_token: str
    app_token: str
    client_id: str
    client_secret: str
    signing_secret: str
    scopes: list[str]
    server: SlackServer


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


class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, dc.Field[Any]]]


DataclassT = TypeVar("DataclassT", bound=DataclassInstance)
Value = str | bool | list


@overload
def from_dict(klass: type[DataclassT], d: dict) -> DataclassT:
    ...


@overload
def from_dict(klass: Any, d: Value) -> Value:
    ...


def from_dict(klass: type[DataclassT], d: dict | Value) -> DataclassT | Value:
    """Parse a dictionary into an instance of the given dataclass

    For example:
        @dc.dataclass
        class SubConfig:
            dorf: str

        @dc.dataclass
        class Config:
            foo: str
            bar: int
            baz: list[str]
            sub: SubConfig

        config = from_dict(Config, {
            "foo": "norf",
            "bar": 123,
            "baz": ["a", "b", "c"],
            "sub": {"dorf": "x"},
        })

    will return an instance of `Config` with the values from the dict
    """
    if not dc.is_dataclass(klass):
        return cast(Value, d)
    if not isinstance(d, dict):
        raise ConfigError("Expected a dictionary")

    fieldtypes = {f.name: f.type for f in dc.fields(klass)}
    if missing := set(fieldtypes.keys()) - set(d.keys()):
        raise MissingKey(
            f"Missing key(s) in {klass.__name__} section: {', '.join(missing)}"
        )
    return klass(**{f: from_dict(fieldtypes[f], d[f]) for f in d})


def from_env(klass: type[DataclassT], base_name: str) -> DataclassT:
    """Parse env into an instance of the given dataclass

    For example:
        @dc.dataclass
        class SubConfig:
            dorf: str

        @dc.dataclass
        class Config:
            foo: str
            bar: int
            baz: list[str]
            sub: SubConfig

        config = from_env(Config, "ENV_EXAMPLE")

    will return an instance of `Config` with values from the environment

    In this example `from_env` will look for the following values:

        * `ENV_EXAMPLE_FOO` -> Config.foo
        * `ENV_EXAMPLE_BAR` -> Config.bar
        * `ENV_EXAMPLE_BAZ` -> Config.baz
        * `ENV_EXAMPLE_SUB__DORF` -> Config.sub.dorf

    If the dataclass field type is not str, it's expected to be json loadable
    """
    fields = {}
    for field in dc.fields(klass):
        if dc.is_dataclass(field.type):
            fields[field.name] = from_env(
                field.type, f"{base_name}_{field.name}_".upper()
            )
        else:
            env_var_name = f"{base_name}_{field.name}".upper()
            if env_var_name not in os.environ:
                raise MissingKey(
                    f"Missing env var for {klass.__name__} section: {env_var_name}"
                )
            env_var = os.environ[env_var_name]
            if field.type != str:
                env_var = json.loads(env_var)
            fields[field.name] = env_var
    return klass(**fields)


# Where to load the config from, supported options:
# * `config.toml`: The default, see config.example.toml
# * `env`: Each
CONFIG_SOURCE = os.environ.get("SIMILARIUM_CONFIG_SOURCE", "config.toml")


_config_path = Path("./config.toml")
with open(_config_path, "r") as f:
    _config = toml.load(f)

config: Config = from_dict(Config, _config)
