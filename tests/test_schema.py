from datetime import date

from schema_validator.domain.schema import (
    ColumnInfo,
    Constraints,
    DataType,
    FormatType,
    TableSchema,
)
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
    with pytest.raises(ValueError, match="does not exist in the columns"):
        TableSchema(name="test_table", columns=columns, primary_key="non_existent_column")


def test_unique_column_names_per_table():
    columns = [
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False),
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=True),
        ColumnInfo(name="id", data_type=DataType.STRING, nullable=False)  # duplicate column name but different type
    ]
    with pytest.raises(ValueError, match="Column names must be unique"):
        TableSchema(name="test_table", columns=columns)


def test_format_only_for_string_data_type():
    with pytest.raises(ValueError, match="Format is only applicable for STRING"):
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False, format=FormatType.EMAIL)


def test_invalid_format_instance_of_format_type():
    with pytest.raises(TypeError, match="Invalid format type"):
        ColumnInfo(name="name", data_type=DataType.STRING, nullable=False, format="not_a_format")

def test_invalid_data_type_instance_of_data_type_enum():
    with pytest.raises(TypeError, match="Invalid data type"):
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


# --- Constraints ---

def test_constraints_with_no_bounds():
    constraints = Constraints()
    assert constraints.min_value is None
    assert constraints.max_value is None
    assert constraints.allowed_values is None


def test_constraints_with_only_one_bound():
    assert Constraints(min_value=0).max_value is None
    assert Constraints(max_value=10).min_value is None


@pytest.mark.parametrize("bound", ["min_value", "max_value"])
def test_bound_must_be_a_comparable_type(bound):
    with pytest.raises(TypeError, match="must be of type float, int, date, time, or datetime"):
        Constraints(**{bound: "not_a_number"})


@pytest.mark.parametrize("bound", ["min_value", "max_value"])
def test_bool_is_rejected_as_a_bound(bound):
    # bool is a subclass of int and must not slip through as a numeric bound.
    with pytest.raises(TypeError, match="must be of type float, int, date, time, or datetime"):
        Constraints(**{bound: True})


def test_allowed_values_must_be_a_list():
    with pytest.raises(TypeError, match="allowed_values must be a list"):
        Constraints(allowed_values="a")


def test_min_greater_than_max():
    with pytest.raises(ValueError, match="min_value must be less than or equal to max_value"):
        Constraints(min_value=50, max_value=10)


def test_min_equal_to_max_is_allowed():
    constraints = Constraints(min_value=10, max_value=10)
    assert constraints.min_value == constraints.max_value


def test_bounds_must_be_comparable_to_each_other():
    with pytest.raises(ValueError, match="min_value and max_value must be comparable"):
        Constraints(min_value=1, max_value=date(2026, 1, 1))


# --- ColumnInfo type checks ---

@pytest.mark.parametrize("name", [123, None, ""])
def test_column_name_must_be_a_non_empty_string(name):
    with pytest.raises(TypeError, match="Column name must be a non-empty string"):
        ColumnInfo(name=name, data_type=DataType.INTEGER, nullable=False)


@pytest.mark.parametrize("nullable", ["yes", 1, None])
def test_nullable_must_be_a_boolean(nullable):
    with pytest.raises(TypeError, match="nullable must be a boolean"):
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=nullable)


def test_column_description_must_be_a_string():
    with pytest.raises(TypeError, match="description must be a string"):
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False, description=["a"])


def test_constraints_must_be_a_constraints_instance():
    with pytest.raises(TypeError, match="constraints must be a Constraints"):
        ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False, constraints={"min_value": 0})


def test_column_accepts_constraints():
    constraints = Constraints(min_value=0, max_value=100)
    column = ColumnInfo(name="score", data_type=DataType.INTEGER, nullable=False, constraints=constraints)
    assert column.constraints is constraints


# --- ColumnInfo allowed_values vs data_type ---

def test_allowed_values_for_string_column_must_be_strings():
    with pytest.raises(ValueError, match="Allowed values for STRING"):
        ColumnInfo(
            name="status",
            data_type=DataType.STRING,
            nullable=False,
            constraints=Constraints(allowed_values=["active", 1]),
        )


def test_allowed_values_for_integer_column_must_be_numbers():
    with pytest.raises(ValueError, match="Allowed values for INTEGER"):
        ColumnInfo(
            name="level",
            data_type=DataType.INTEGER,
            nullable=False,
            constraints=Constraints(allowed_values=[1, "two"]),
        )


def test_bool_is_rejected_in_allowed_values_for_integer_column():
    with pytest.raises(ValueError, match="Allowed values for INTEGER"):
        ColumnInfo(
            name="level",
            data_type=DataType.INTEGER,
            nullable=False,
            constraints=Constraints(allowed_values=[1, True]),
        )


def test_valid_allowed_values_are_accepted():
    column = ColumnInfo(
        name="status",
        data_type=DataType.STRING,
        nullable=False,
        constraints=Constraints(allowed_values=["active", "closed"]),
    )
    assert column.constraints.allowed_values == ["active", "closed"]


# --- TableSchema type checks ---

@pytest.mark.parametrize("name", [123, None, ""])
def test_table_name_must_be_a_non_empty_string(name):
    columns = [ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False)]
    with pytest.raises(TypeError, match="Table name must be a non-empty string"):
        TableSchema(name=name, columns=columns)


def test_columns_must_be_a_list():
    column = ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False)
    with pytest.raises(TypeError, match="columns must be a list"):
        TableSchema(name="test_table", columns=column)


def test_every_column_must_be_a_column_info():
    with pytest.raises(TypeError, match="Every column must be a ColumnInfo"):
        TableSchema(name="test_table", columns=[{"name": "id"}])


@pytest.mark.parametrize("primary_key", [["id", "tenant"], 123])
def test_primary_key_must_be_a_string(primary_key):
    columns = [ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False)]
    with pytest.raises(TypeError, match="primary_key must be a string"):
        TableSchema(name="test_table", columns=columns, primary_key=primary_key)


def test_table_description_must_be_a_string():
    columns = [ColumnInfo(name="id", data_type=DataType.INTEGER, nullable=False)]
    with pytest.raises(TypeError, match="description must be a string"):
        TableSchema(name="test_table", columns=columns, description=["a"])


def test_table_schema_must_have_at_least_one_column():
    with pytest.raises(ValueError, match="A table schema must have at least one column"):
        TableSchema(name="test_table", columns=[])