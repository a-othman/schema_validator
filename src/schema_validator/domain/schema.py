from dataclasses import dataclass
from enum import Enum
from datetime import date, time, datetime
class FormatType(Enum):
    EMAIL = "email"
    URL = "url"
    BINARY = "binary"
    UUID = "uuid"

class DataType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    STRING = "string"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"

    BIGINT = "bigint"
    SMALLINT = "smallint"
    TIME = "time"
    TIMESTAMP_TZ = "timestamp_tz"

# int/float/date/time/datetime are the comparable bound types.
# bool is excluded deliberately — it's a subclass of int and must not
# slip through as a numeric bound.
_BOUND_TYPES = (int, float, date, time, datetime)


@dataclass
class Constraints:
    min_value: float | int | date | time | datetime | None = None
    max_value: float | int | date | time | datetime | None = None
    allowed_values: list[str | int | float | bool] | None = None

@dataclass
class ColumnInfo:
    name: str
    data_type: DataType
    nullable: bool
    format: FormatType | None = None
    description: str | None = None
    constraints: Constraints | None = None

    def __post_init__(self):
        if not isinstance(self.data_type, DataType):
            raise TypeError(f"Invalid data type: {self.data_type}. Must be an instance of DataType Enum.")

        if self.data_type != DataType.STRING and self.format is not None:
            raise ValueError(
                f"Format is only applicable for STRING data type. Got {self.data_type} instead.")

        if (
            self.data_type == DataType.STRING
            and self.format is not None
            and not isinstance(self.format, FormatType)
        ):
            raise TypeError(
                f"Invalid format type: {self.format}. Must be an instance of FormatType Enum."
            )

        if self.constraints is None:
            return

        # Fix #2 + #3: bounds are optional; type-check only when present,
        # and reject bool explicitly (bool is a subclass of int).
        for label, value in (
            ("min_value", self.constraints.min_value),
            ("max_value", self.constraints.max_value),
        ):
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, _BOUND_TYPES):
                raise ValueError(
                    f"{label} must be of type float, int, date, time, or datetime."
                )

        # Fix #3: guard cross-type comparison so it raises ValueError, not TypeError.
        min_v, max_v = self.constraints.min_value, self.constraints.max_value
        if min_v is not None and max_v is not None:
            try:
                mismatched = min_v > max_v
            except TypeError as e:
                raise ValueError(
                    f"min_value and max_value must be comparable: {e}"
                ) from e
            if mismatched:
                raise ValueError("min_value must be less than or equal to max_value.")

        if self.data_type == DataType.STRING and self.constraints.allowed_values is not None:
            if not all(isinstance(v, str) for v in self.constraints.allowed_values):
                raise ValueError("Allowed values for STRING data type must be strings.")

        if self.data_type == DataType.INTEGER and self.constraints.allowed_values is not None:
            if not all(
                isinstance(v, (int, float)) and not isinstance(v, bool)
                for v in self.constraints.allowed_values
            ):
                raise ValueError("Allowed values for INTEGER data type must be integers or floats.")


@dataclass
class TableSchema:
    name: str
    columns: list[ColumnInfo]
    primary_key: str | None = None
    description: str | None = None

    def __post_init__(self):
        if not self.columns:
            raise ValueError("A table schema must have at least one column.")

        if self.primary_key and not any(col.name == self.primary_key for col in self.columns):
            raise ValueError(f"Primary key '{self.primary_key}' does not exist in the columns.")

        column_names = [col.name for col in self.columns]
        if len(column_names) != len(set(column_names)):
            raise ValueError("Column names must be unique within a table schema.")