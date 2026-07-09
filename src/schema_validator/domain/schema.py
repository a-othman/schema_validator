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
        

        c= self.constraints
        has_range= c.min_value is not None or c.max_value is not None

        if has_range and self.data_type not in RANGE_ALLOWED:
            raise ValueError(f'Range is not applicable for {self.data_type}')

        if c.min_value is not None and not is_compatible(c.min_value, self.data_type):
            raise TypeError('min_value must have same type')

        if c.max_value is not None and not is_compatible(c.max_value, self.data_type):
            raise TypeError('max_value must have same type')
        
        if c.min_value is not None and c.max_value is not None and c.min_value > c.max_value:
                raise ValueError("min_value must be <= max_value")
            
        if c.allowed_values is not None:
            if any(not is_compatible(v, self.data_type) for v in c.allowed_values):
                raise ValueError(f"allowed value for {self.data_type} must all have compatiable type")

        

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



RANGE_ALLOWED= (DataType.INTEGER, DataType.FLOAT, DataType.DECIMAL, 
                DataType.BIGINT, DataType.SMALLINT, 
                DataType.DATE, DataType.TIME, DataType.TIMESTAMP, DataType.TIMESTAMP_TZ)



DATATYPE_TO_PYTHON: dict[DataType, tuple[type, ...]] = {
    DataType.INTEGER: (int,),
    DataType.BIGINT: (int,),
    DataType.SMALLINT: (int,),
    DataType.FLOAT: (int, float),
    DataType.DECIMAL: (int, float),
    DataType.STRING: (str,),
    DataType.BOOLEAN: (bool,),
    DataType.DATE: (date,),
    DataType.TIME: (time,),
    DataType.TIMESTAMP: (datetime,),
    DataType.TIMESTAMP_TZ: (datetime,),
}


def is_compatible(value, data_type: DataType) -> bool:
    """True if `value` is an acceptable Python value for a column of `data_type`."""
    allowed = DATATYPE_TO_PYTHON.get(data_type)
    if allowed is None:
        raise ValueError(f"No Python-type mapping for {data_type}")

    # bool is a subclass of int — keep it out of numeric types
    if bool not in allowed and isinstance(value, bool):
        return False

    # datetime is a subclass of date — keep timestamps out of DATE
    if data_type == DataType.DATE and isinstance(value, datetime):
        return False

    return isinstance(value, allowed)