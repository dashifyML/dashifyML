from enum import Enum
import pandas as pd
from typing import Dict
import dateutil.parser
import json

class SupportedDataTypes(Enum):
    int_type = 1
    float_type = 2
    string_type = 3
    list_type = 4
    bool_type = 5
    datetime = 6


def infer_datatypes_for_columns(df: pd.DataFrame) -> Dict[str, SupportedDataTypes]:
    def infer_datatye(col_series: pd.Series, df_col_type):
        if df_col_type == "float64":
            return SupportedDataTypes.float_type
        elif df_col_type == "int64":
            return SupportedDataTypes.int_type
        elif df_col_type == "bool":
            return SupportedDataTypes.bool_type
        elif df_col_type == "object" and (col_series.apply(type) == list).all():
                return SupportedDataTypes.list_type
        else:
            return SupportedDataTypes.string_type

    cols = df.columns
    col_type_series = df.dtypes
    return {col: infer_datatye(df[col], col_type_series[col]) for col in cols}


def convert_string_to_supported_data_type(value: str, data_type: SupportedDataTypes):
    if data_type == SupportedDataTypes.string_type:
        return value
    elif data_type == SupportedDataTypes.int_type:
        return int(value)
    elif data_type == SupportedDataTypes.float_type:
        return float(value)
    elif data_type == SupportedDataTypes.bool_type:
        return value.lower() == "true"
    elif data_type == SupportedDataTypes.datetime:
        return dateutil.parser.parse(value)
    elif data_type == SupportedDataTypes.list_type:
        return json.loads(value)
