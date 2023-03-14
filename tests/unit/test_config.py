import dataclasses as dc
import os
from unittest import mock

import pytest

from similarium.config import MissingKey, from_dict, from_env


def test_from_dict_with_dataclass():
    @dc.dataclass
    class Sub:
        norf: str
        lst: list[str]

    @dc.dataclass
    class Config:
        foo: str
        bar: str
        sub: Sub

    config = from_dict(
        Config,
        {
            "foo": "baz",
            "bar": "qux",
            "sub": {
                "norf": "dorf",
                "lst": ["a", "b", "c"],
            },
        },
    )

    assert config.foo == "baz"
    assert config.bar == "qux"
    assert config.sub.norf == "dorf"
    assert config.sub.lst == ["a", "b", "c"]


def test_from_dict_with_dataclass_missing_fields():
    @dc.dataclass
    class Config:
        foo: str
        bar: str

    with pytest.raises(MissingKey, match="Missing key\\(s\\) in Config section: bar"):
        from_dict(
            Config,
            {
                "foo": "baz",
            },
        )


def test_from_env_with_dataclass():
    @dc.dataclass
    class Sub:
        norf: str
        lst: list[str]

    @dc.dataclass
    class Config:
        foo: str
        bar: str
        baz: int
        sub: Sub

    with mock.patch.dict(
        os.environ,
        {
            "TEST_FOO": "hello",
            "TEST_BAR": "world",
            "TEST_BAZ": "123",
            "TEST_SUB__NORF": "sub_string",
            "TEST_SUB__LST": '["1", "2", "3"]',
        },
    ):
        config = from_env(Config, "TEST")

    assert config.foo == "hello"
    assert config.bar == "world"
    assert config.baz == 123
    assert config.sub.norf == "sub_string"
    assert config.sub.lst == ["1", "2", "3"]


def test_from_env_with_dataclass_missing_fields():
    @dc.dataclass
    class Config:
        foo: str
        bar: str

    os.environ["TEST_FOO"] = "hello"

    with pytest.raises(
        MissingKey, match="Missing env var for Config section: TEST_BAR"
    ):
        with mock.patch.dict(os.environ, {"TEST_FOO": "hello"}):
            from_env(Config, "TEST")
