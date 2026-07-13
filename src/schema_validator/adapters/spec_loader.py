import json
import yaml
from pathlib import Path

from schema_validator.domain.schema import (
    Constraints,
    ColumnInfo,
    DataType,
    FormatType,
    TableSchema,
)


_YAML_SUFFIXES = {".yaml", ".yml"}
_JSON_SUFFIXES = {".json"}
_SUPPORTED_SUFFIXES = _YAML_SUFFIXES | _JSON_SUFFIXES

class SpecError(Exception):
    """Raised when a spec file's content or format is invalid."""


def _read_yaml(text: str, path: Path) -> dict:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise SpecError(f"Invalid YAML in {path}: {e}") from e

    if data is None:                 # empty file
        raise SpecError(f"Spec file is empty: {path}")
    if not isinstance(data, dict):
        raise SpecError(
            f"Spec root must be a mapping in {path}, got {type(data).__name__}"
        )
    return data


def _read_json(text: str, path: Path) -> dict:
    if not text.strip():             # empty file
        raise SpecError(f"Spec file is empty: {path}")

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise SpecError(f"Invalid JSON in {path}: {e}") from e

    if not isinstance(data, dict):
        raise SpecError(
            f"Spec root must be a mapping in {path}, got {type(data).__name__}"
        )
    return data



def _read(path: Path) -> dict:
    suffix = path.suffix.lower()
    if suffix in _YAML_SUFFIXES:
        reader = _read_yaml
    elif suffix in _JSON_SUFFIXES:
        reader = _read_json
    else:
        supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
        raise SpecError(
            f"Unsupported spec format '{suffix}'. Supported: {supported}"
        )

    text = path.read_text()
    return reader(text, path)


def _check_keys(
    data: dict, *, required: set[str], optional: set[str], where: str, path: Path
) -> None:
    keys = set(data)
    unknown = keys - (required | optional)
    if unknown:
        raise SpecError(
            f"Unknown key(s) {sorted(unknown)} in {where} ({path}). "
            f"Allowed: {sorted(required | optional)}"
        )
    missing = required - keys
    if missing:
        raise SpecError(f"Missing required key(s) {sorted(missing)} in {where} ({path})")


def _to_constraints(raw: dict, column: str, path: Path) -> Constraints:
    if not isinstance(raw, dict):
        raise SpecError(
            f"'constraints' must be a mapping for column '{column}' in {path}, "
            f"got {type(raw).__name__}"
        )
    _check_keys(
        raw,
        required=set(),
        optional={"min_value", "max_value", "allowed_values"},
        where=f"constraints of column '{column}'",
        path=path,
    )
    return Constraints(
        min_value=raw.get("min_value"),
        max_value=raw.get("max_value"),
        allowed_values=raw.get("allowed_values"),
    )


def _to_column(raw: dict, path: Path) -> ColumnInfo:
    if not isinstance(raw, dict):
        raise SpecError(f"Each column must be a mapping in {path}, got {type(raw).__name__}")
    _check_keys(
        raw,
        required={"name", "data_type", "nullable"},
        optional={"format", "description", "constraints"},
        where="column",
        path=path,
    )
    name = raw["name"]

    try:
        data_type = DataType(raw["data_type"])
    except ValueError as e:
        raise SpecError(
            f"Invalid data_type '{raw['data_type']}' for column '{name}' in {path}. "
            f"Allowed: {[d.value for d in DataType]}"
        ) from e

    nullable = raw["nullable"]
    if not isinstance(nullable, bool):
        raise SpecError(
            f"'nullable' must be a boolean for column '{name}' in {path}, "
            f"got {type(nullable).__name__}"
        )

    fmt = None
    if "format" in raw:
        try:
            fmt = FormatType(raw["format"])
        except ValueError as e:
            raise SpecError(
                f"Invalid format '{raw['format']}' for column '{name}' in {path}. "
                f"Allowed: {[f.value for f in FormatType]}"
            ) from e

    constraints = _to_constraints(raw["constraints"], name, path) if "constraints" in raw else None

    try:
        return ColumnInfo(
            name=name,
            data_type=data_type,
            nullable=nullable,
            format=fmt,
            description=raw.get("description"),
            constraints=constraints,
        )
    except (ValueError, TypeError) as e:
        raise SpecError(f"Invalid column '{name}' in {path}: {e}") from e


def _to_schema(raw: dict, path: Path) -> TableSchema:
    _check_keys(
        raw,
        required={"name", "columns"},
        optional={"primary_key", "description"},
        where="table",
        path=path,
    )
    columns_raw = raw["columns"]
    if not isinstance(columns_raw, list):
        raise SpecError(f"'columns' must be a list in {path}, got {type(columns_raw).__name__}")
    columns = [_to_column(c, path) for c in columns_raw]

    try:
        return TableSchema(
            name=raw["name"],
            columns=columns,
            primary_key=raw.get("primary_key"),
            description=raw.get("description"),
        )
    except (ValueError, TypeError) as e:
        raise SpecError(f"Invalid table schema in {path}: {e}") from e


def load_schema(path: Path) -> TableSchema:
    return _to_schema(_read(path), path)