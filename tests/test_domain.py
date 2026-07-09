from schema_validator.domain.schema import (
        ColumnInfo, TableSchema, DataType, FormatType, Constraints, is_compatible )
import pytest
from datetime import date, time, datetime

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
    assert column_info.format == FormatType.EMAIL
    assert column_info.description == "User email address"


# ---------- is_compatible (pure helper, table-driven) ----------

@pytest.mark.parametrize("value, data_type, expected", [
    # numerics accept int
    (5, DataType.INTEGER, True),
    (5, DataType.BIGINT, True),
    (5, DataType.SMALLINT, True),
    (5, DataType.FLOAT, True),
    (5.0, DataType.FLOAT, True),
    (5.0, DataType.DECIMAL, True),
    # bool rejected by numerics, accepted by BOOLEAN
    (True, DataType.INTEGER, False),
    (True, DataType.FLOAT, False),
    (True, DataType.BOOLEAN, True),
    # temporal
    (date(2024, 1, 1), DataType.DATE, True),
    (datetime(2024, 1, 1), DataType.DATE, False),   # datetime is NOT a valid date-only
    (datetime(2024, 1, 1), DataType.TIMESTAMP, True),
    (datetime(2024, 1, 1), DataType.TIMESTAMP_TZ, True),
    (time(14, 30), DataType.TIME, True),
    # cross-type mismatches
    ("x", DataType.INTEGER, False),
    (5, DataType.STRING, False),
])
def test_is_compatible(value, data_type, expected):
    assert is_compatible(value, data_type) is expected


# range applies only to numeric/temporal types

def test_range_not_allowed_on_string():
    with pytest.raises(ValueError, match=r"Range is not applicable"):
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=False,
                   constraints=Constraints(min_value=1, max_value=10))

def test_range_not_allowed_on_boolean():
    with pytest.raises(ValueError, match=r"Range is not applicable"):
        ColumnInfo(name="flag", data_type=DataType.BOOLEAN, nullable=False,
                   constraints=Constraints(min_value=0, max_value=1))

def test_range_allowed_on_integer_constructs():
    col = ColumnInfo(name="age", data_type=DataType.INTEGER, nullable=False,
                     constraints=Constraints(min_value=0, max_value=120))
    assert col.constraints.min_value == 0
    assert col.constraints.max_value == 120


# range bound compatibility with data_type

def test_range_bound_incompatible_type_raises():
    with pytest.raises(TypeError, match=r"min_value must have same type"):
        ColumnInfo(name="age", data_type=DataType.INTEGER, nullable=False,
                   constraints=Constraints(min_value=date(2024, 1, 1),
                                           max_value=date(2025, 1, 1)))

def test_date_range_on_date_column_constructs():
    col = ColumnInfo(name="d", data_type=DataType.DATE, nullable=False,
                     constraints=Constraints(min_value=date(2024, 1, 1),
                                             max_value=date(2025, 1, 1)))
    assert col.constraints.max_value == date(2025, 1, 1)

# min <= max
def test_min_greater_than_max_raises():
    with pytest.raises(ValueError, match=r"min_value must be <= max_value"):
        ColumnInfo(name="age", data_type=DataType.INTEGER, nullable=False,
                   constraints=Constraints(min_value=100, max_value=0))

def test_min_equal_max_is_allowed():   # boundary: > not >=
    col = ColumnInfo(name="age", data_type=DataType.INTEGER, nullable=False,
                     constraints=Constraints(min_value=5, max_value=5))
    assert col.constraints.min_value == 5
    assert col.constraints.max_value == 5

def test_only_min_set_constructs():
    col = ColumnInfo(name="age", data_type=DataType.INTEGER, nullable=False,
                     constraints=Constraints(min_value=0))
    assert col.constraints.max_value is None
    assert col.constraints.min_value == 0


# allowed_values compatibility
def test_allowed_values_all_compatible_constructs():
    col = ColumnInfo(name="status", data_type=DataType.STRING, nullable=False,
                     constraints=Constraints(allowed_values=["active", "inactive"]))
    assert col.constraints.allowed_values == ["active", "inactive"]

def test_allowed_values_wrong_type_in_string_raises():
    with pytest.raises(ValueError, match=r"must all have compatiable type"):
        ColumnInfo(name="status", data_type=DataType.STRING, nullable=False,
                   constraints=Constraints(allowed_values=["active", 5]))

def test_allowed_values_bool_in_integer_raises():   # subclass trap
    with pytest.raises(ValueError, match=r"must all have compatiable type"):
        ColumnInfo(name="n", data_type=DataType.INTEGER, nullable=False,
                   constraints=Constraints(allowed_values=[1, True]))


# no constraints (guards the None early-return)
def test_column_with_none_constraints_constructs():
    col = ColumnInfo(name="x", data_type=DataType.INTEGER, nullable=False)
    assert col.constraints is None