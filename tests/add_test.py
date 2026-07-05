from schema_validator.schema import ColumnInfo, TableSchema, DataType, FormatType
import pytest

def test_column_info_creation_with_only_required_args():
    column_info = ColumnInfo(name="email", data_type=DataType.STRING, nullable=False)
    assert column_info.name == "email"
    assert column_info.data_type == DataType.STRING
    assert column_info.nullable == False
    assert column_info.format is None
    assert column_info.description is None

def test_table_schema_with_pk_none():
    columns = [
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False),
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=True)
    ]
    table_schema = TableSchema(name="test_table", columns=columns, primary_key=None)
    assert table_schema.name == "test_table"
    assert len(table_schema.columns) == 2
    assert table_schema.description is None
    assert table_schema.primary_key is None

def test_primary_key_exists_in_columns():
    columns = [
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False),
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=True)
    ]
    with pytest.raises(ValueError, match= r"Primary key '.*' does not exist in the columns."):
        TableSchema(name="test_table", columns=columns, primary_key="non_existent_column")


def test_unique_column_names_per_table():
    columns = [
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False),
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=True),
        ColumnInfo(name="id", data_type=DataType.STRING, nullable=False)  # duplicate column name but different type
    ]
    with pytest.raises(ValueError, match= "Column names must be unique within a table schema."):
        TableSchema(name="test_table", columns=columns)


def test_format_only_for_string_data_type():
    with pytest.raises(ValueError, match= r"Format is only applicable for STRING data type. Got DataType.* instead."):
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False, format=FormatType.EMAIL)


def test_invalid_format_instance_of_format_type():
    with pytest.raises(TypeError, match= r"Invalid format type: .* Must be an instance of FormatType Enum."):
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=False, format="not_a_format")

def test_invalid_data_type_instance_of_data_type_enum():
    with pytest.raises(TypeError, match= r"Invalid data type: .* Must be an instance of DataType Enum."):
        ColumnInfo(name="id", data_type="not_a_data_type", nullable=False)

def test_table_schema_creation_with_valid_inputs():
    columns = [
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False),
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=True)
    ]
    table_schema = TableSchema(name="test_table", columns=columns, primary_key="id")
    assert table_schema.name == "test_table"
    assert len(table_schema.columns) == 2
    assert table_schema.primary_key == "id"

def test_column_info_creation_with_valid_inputs():
    column_info = ColumnInfo(name="email", data_type=DataType.STRING, nullable=False, format=FormatType.EMAIL, description="User email address")
    assert column_info.name == "email"
    assert column_info.data_type == DataType.STRING
    assert column_info.nullable == False
    assert column_info.format == FormatType.NOTHING
    assert column_info.description == "User email address"