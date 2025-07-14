"""Common types and functions for models."""
# pylint: disable=W1203, E1101, W0212
import logging
from datetime import datetime
from typing import Literal, Optional

import orjson
import pandas as pd  # type: ignore
from pydantic import AliasChoices, BaseModel, Field
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

logger = logging.getLogger("openalex-types.common")
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Set the level for the handler
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def no_tz(dt: datetime) -> str:
    """Make sure no time zone is present in the datetime."""
    return datetime.fromisoformat(dt.strftime("%Y-%m-%d %H:%M:%S")).isoformat(sep="T")


def check_8601(dt: datetime) -> str:
    """Check ISO 8601 format."""
    return dt.isoformat()


DateTimeNoTZ = Annotated[datetime, AfterValidator(no_tz)]
Date8601 = Annotated[datetime, AfterValidator(check_8601)]

CountryCode = Annotated[str, Field(..., min_length=2, max_length=2)]


class OpenAlexObject(BaseModel):
    """Base OpenAlex Object."""
    id: str


class SQLTable:
    """Classes that represent SQL tables."""
    _sql_order: list[str]

    def _get_arg(self, arg_name: str) -> str:
        """Get arg_name if it exists."""
        try:
            arg = getattr(self, arg_name)
            if arg is None:
                return "NULL"
            if isinstance(arg, list):
                if len(arg) == 0:
                    return "NULL"
                if isinstance(arg[0], str):
                    ls = ",".join(
                        ["\"" + x.replace("'", "''") + "\"" for x in arg])
                    return f"'[{ls}]'"
                if isinstance(arg[0], (int, float)):
                    return f"'{arg}'"
            if isinstance(arg, bool):
                return str(arg).upper()
            if isinstance(arg, (int, float)):
                return str(arg)
            if isinstance(arg, dict):
                s = orjson.dumps(arg).decode().replace("'", "''")
                return f"'{s}'"
            s = str(arg).replace("'", "''")
        except Exception as e:
            logger.error(f"Error with _getarg{arg_name}: {e}. Arg is {arg}")
            raise e
        return f"'{s}'"

    @property
    def sql_columns(self) -> str:
        """SQL string for columns."""
        return "(" + ", ".join(self._sql_order) + ")"

    @property
    def sql_values(self) -> str:
        """SQL string for INSERT."""
        return "(" + ", ".join([self._get_arg(k) for k in self._sql_order]) + ")"

    def to_sql_values(self) -> tuple:
        """Return a tuple of values for parameterized SQL queries."""
        values = []
        for key in self._sql_order:
            value = getattr(self, key, None)
            # Convert dictionaries to JSON strings for asyncpg
            if isinstance(value, dict):
                value = orjson.dumps(value).decode()
            # Convert ISO datetime strings back to datetime objects for PostgreSQL
            elif isinstance(value, str) and value and len(value) >= 10:
                # Check if it looks like an ISO datetime string
                if value[4] == '-' and value[7] == '-':
                    try:
                        # Try to parse as datetime
                        if 'T' in value or ' ' in value:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        # If it's just a date, parse as date
                        else:
                            value = datetime.fromisoformat(value + 'T00:00:00')
                    except (ValueError, AttributeError):
                        # If parsing fails, keep as string
                        pass
            values.append(value)
        return tuple(values)


def sql_tables_to_df(tables: list[SQLTable]) -> pd.DataFrame:
    """Convert SQL tables to DataFrame."""
    list_ = [orjson.loads(x.model_dump_json(include=x._sql_order))  # type: ignore
             for x in tables]
    df = pd.DataFrame(list_)
    return df


class BaseCountByYear(BaseModel):
    """Base Count by Year."""
    year: int
    works_count: Optional[int] = None
    cited_by_count: Optional[int] = None
    oa_works_count: Optional[int] = None


class SummaryStats(BaseModel):
    """Citation Metrics."""
    twoyr_mean_citedness: Optional[float] = Field(
        None, validation_alias=AliasChoices("2yr_mean_citedness"))
    h_index: Optional[int] = None
    i10_index: Optional[int] = None


class Role(BaseModel):
    """Role Object."""
    role: Literal["institution", "funder", "publisher"]
    id: str
    works_count: int
