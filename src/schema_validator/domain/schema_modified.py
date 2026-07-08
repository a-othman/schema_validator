NUMERIC_TYPES = (int, float)
TEMPORAL_TYPES = (date, time, datetime)

# Adjust these to your actual DataType members
RANGE_ALLOWED = {
    DataType.INTEGER, DataType.FLOAT,
    DataType.DATE, DataType.TIME, DataType.TIMESTAMP,
}

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
            raise TypeError(f"Invalid data type: {self.data_type}. Must be a DataType Enum.")

        # format ↔ STRING coupling
        if self.data_type != DataType.STRING and self.format is not None:
            raise ValueError(f"Format is only applicable for STRING. Got {self.data_type}.")
        
        if self.data_type == DataType.STRING and self.format is not None \
                and not isinstance(self.format, FormatType):
            raise TypeError(f"Invalid format type: {self.format}. Must be a FormatType Enum.")

        # everything below concerns constraints — bail early if absent
        if self.constraints is None:
            return

        c = self.constraints
        has_range = c.min_value is not None or c.max_value is not None

        # range only makes sense on numeric/temporal columns
        if has_range and self.data_type not in RANGE_ALLOWED:
            raise ValueError(f"Range is not applicable for {self.data_type}.")

        # min <= max, only when both are present
        if c.min_value is not None and c.max_value is not None:
            if type(c.min_value) is not type(c.max_value):
                raise ValueError("min_value and max_value must be the same type.")
            if c.min_value > c.max_value:
                raise ValueError("min_value must be <= max_value.")

        # allowed_values type-compatibility
        if c.allowed_values is not None:
            if self.data_type == DataType.STRING:
                if any(not isinstance(v, str) for v in c.allowed_values):
                    raise ValueError("Allowed values for STRING must all be strings.")
            elif self.data_type == DataType.INTEGER:
                if any(not isinstance(v, int) or isinstance(v, bool) for v in c.allowed_values):
                    raise ValueError("Allowed values for INTEGER must all be integers.")