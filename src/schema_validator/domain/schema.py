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
            raise ValueError(f"Format is only applicable for STRING data type. Got {self.data_type} instead.")
        
        if self.data_type == DataType.STRING and self.format is not None and not isinstance(self.format, FormatType):
            raise TypeError(f"Invalid format type: {self.format}. Must be an instance of FormatType Enum.")
        
        if self.constraints is None:
            return
        
        
        
        if not isinstance(self.constraints.min_value, (float, int, date, time, datetime)) or \
                not isinstance(self.constraints.max_value, (float, int, date, time, datetime)):
            raise ValueError("min_value and max_value must be of type float, int, date, time, datetime")
        
        if self.constraints.min_value> self.constraints.max_value:
            raise ValueError("Min value should me smaller than max value")    
        
        if self.data_type == DataType.STRING and self.constraints.allowed_values is not None:
            if not any(isinstance(value, str) for value in self.constraints.allowed_values):
                raise ValueError("Allowed values for STRING data type must be strings.")

        if self.data_type == DataType.INTEGER and self.constraints.allowed_values is not None:
            if not any(isinstance(value, (int, float)) for value in self.constraints.allowed_values):
                raise ValueError("Allowed values for INTEGER data type must be integers or floats.")
        

        


        

@dataclass
class TableSchema:
    name: str
    columns: list[ColumnInfo]
    primary_key: str | None = None
    description: str | None = None

    def __post_init__(self):
        if self.primary_key and not any(col.name == self.primary_key for col in self.columns):
            raise ValueError(f"Primary key '{self.primary_key}' does not exist in the columns.")
        
        columns_names=[col.name for col in self.columns]
        if len(columns_names) != len(set(columns_names)):
            raise ValueError("Column names must be unique within a table schema.")
