from dataclasses import dataclass
from enum import Enum

class FormatType(Enum):
    EMAIL = "email"
    URL = "url"
    BINARY = "binary"
    UUID = "uuid"

@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool
    format: FormatType | None = None
    description: str | None = None

    def __post_init__(self):
        if self.format is not None and not isinstance(self.format, FormatType):
            raise TypeError(f"Invalid format type: {self.format}. Must be an instance of FormatType Enum.")

@dataclass
class TableSchema:
    name: str
    columns: list[ColumnInfo]
    primary_key: str | None = None
    description: str | None = None

    def __post_init__(self):
        if self.primary_key and not any(col.name == self.primary_key for col in self.columns):
            raise ValueError(f"Primary key '{self.primary_key}' does not exist in the columns.")

if __name__ == "__main__":
    columns = [
        ColumnInfo(name="id", data_type="int", nullable=False, description="User ID",),
        ColumnInfo(name="name", data_type="varchar", nullable=False, description="User Name"),
        ColumnInfo(name="email", data_type="varchar", format=FormatType.EMAIL, nullable=True, description="User Email")
    ]
    
    table_schema = TableSchema(name="users", columns=columns, description="User information table", primary_key="id")
    print(table_schema)

