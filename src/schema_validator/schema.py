from dataclasses import dataclass
from enum import Enum

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
    

@dataclass
class ColumnInfo:
    name: str
    data_type: DataType
    nullable: bool
    format: FormatType | None = None
    description: str | None = None

    def __post_init__(self):
        if self.format is not None and not isinstance(self.format, FormatType):
            raise TypeError(f"Invalid format type: {self.format}. Must be an instance of FormatType Enum.")

        if not isinstance(self.data_type, DataType):
            raise TypeError(f"Invalid data type: {self.data_type}. Must be an instance of DataType Enum.")

@dataclass
class TableSchema:
    name: str
    columns: list[ColumnInfo]
    primary_key: str | None = None
    description: str | None = None

    def __post_init__(self):
        if self.primary_key and not any(col.name == self.primary_key for col in self.columns):
            raise ValueError(f"Primary key '{self.primary_key}' does not exist in the columns.")
