from collections.abc import Mapping
from typing import TypeAlias

JSONValue: TypeAlias = (
    str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
)


def normalize_json_value(value: object) -> JSONValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [normalize_json_value(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): normalize_json_value(item) for key, item in value.items()}
    return str(value)