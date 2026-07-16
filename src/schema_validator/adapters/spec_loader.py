import json
from enum import Enum
from pathlib import Path
from typing import TypeVar

import yaml

from schema_validator.domain.schema import (
    ColumnInfo,
    Constraints,
    DataType,
    FormatType,
    TableSchema,
)

_YAML_SUFFIXES = {".yaml", ".yml"}
_JSON_SUFFIXES = {".json"}
_SUPPORTED_SUFFIXES = _YAML_SUFFIXES | _JSON_SUFFIXES

E = TypeVar("E", bound=Enum)


class SpecError(Exception):
    """Raised when a spec file's content or format is invalid."""


def _read_yaml(text: str) -> object:
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise SpecError(f"Invalid YAML: {e}") from e


def _read_json(text: str) -> object:
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise SpecError(f"Invalid JSON: {e}") from e


def _read(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix in _YAML_SUFFIXES:
        reader = _read_yaml
    elif suffix in _JSON_SUFFIXES:
        reader = _read_json
    else:
        supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
        raise SpecError(f"Unsupported spec format '{suffix}'. Supported: {supported}")

    text = path.read_text()
    if not text.strip():
        raise SpecError("Spec file is empty")

    data = reader(text)
    if not isinstance(data, dict):
        raise SpecError(f"Spec root must be a mapping, got {type(data).__name__}")
    return data


def _check_keys(data: dict, *, required: set[str], optional: set[str]) -> None:
    keys = set(data)
    unknown = keys - (required | optional)
    if unknown:
        raise SpecError(
            f"Unknown key(s) {sorted(unknown)}. Allowed: {sorted(required | optional)}"
        )
    missing = required - keys
    if missing:
        raise SpecError(f"Missing required key(s) {sorted(missing)}")


def _to_enum(enum_cls: type[E], value: object, field: str) -> E:
    try:
        return enum_cls(value)
    except (ValueError, TypeError) as e:
        raise SpecError(
            f"Invalid {field} {value!r}. Allowed: {[m.value for m in enum_cls]}"
        ) from e


def _column_label(index: int, raw: object) -> str:
    # The index always exists; the name may be missing or malformed, which is
    # itself one of the errors this label has to survive.
    name = raw.get("name") if isinstance(raw, dict) else None
    suffix = f" ({name!r})" if isinstance(name, str) else ""
    return f"columns[{index}]{suffix}"


def _to_constraints(raw: object) -> Constraints:
    if not isinstance(raw, dict):
        raise SpecError(f"Must be a mapping, got {type(raw).__name__}")

    _check_keys(
        raw,
        required=set(),
        optional={"min_value", "max_value", "allowed_values"},
    )
    try:
        return Constraints(
            min_value=raw.get("min_value"),
            max_value=raw.get("max_value"),
            allowed_values=raw.get("allowed_values"),
        )
    except (ValueError, TypeError) as e:
        raise SpecError(str(e)) from e


def _to_column(raw: object) -> ColumnInfo:
    if not isinstance(raw, dict):
        raise SpecError(f"Must be a mapping, got {type(raw).__name__}")

    _check_keys(
        raw,
        required={"name", "data_type", "nullable"},
        optional={"format", "description", "constraints"},
    )

    data_type = _to_enum(DataType, raw["data_type"], "data_type")
    fmt = _to_enum(FormatType, raw["format"], "format") if "format" in raw else None

    constraints = None
    if "constraints" in raw:
        try:
            constraints = _to_constraints(raw["constraints"])
        except SpecError as e:
            raise SpecError(f"constraints: {e}") from e

    try:
        return ColumnInfo(
            name=raw["name"],
            data_type=data_type,
            nullable=raw["nullable"],
            format=fmt,
            description=raw.get("description"),
            constraints=constraints,
        )
    except (ValueError, TypeError) as e:
        raise SpecError(str(e)) from e


def _to_schema(raw: dict) -> TableSchema:
    _check_keys(
        raw,
        required={"name", "columns"},
        optional={"primary_key", "description"},
    )

    columns_raw = raw["columns"]
    if not isinstance(columns_raw, list):
        raise SpecError(f"'columns' must be a list, got {type(columns_raw).__name__}")

    columns = []
    for i, c in enumerate(columns_raw):
        try:
            columns.append(_to_column(c))
        except SpecError as e:
            raise SpecError(f"{_column_label(i, c)}: {e}") from e

    try:
        return TableSchema(
            name=raw["name"],
            columns=columns,
            primary_key=raw.get("primary_key"),
            description=raw.get("description"),
        )
    except (ValueError, TypeError) as e:
        raise SpecError(str(e)) from e


def load_schema(path: Path) -> TableSchema:
    try:
        return _to_schema(_read(path))
    except SpecError as e:
        raise SpecError(f"{path}: {e}") from e
