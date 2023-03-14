import dataclasses as dc

import pytest

from similarium.config import MissingKey, from_dict


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
