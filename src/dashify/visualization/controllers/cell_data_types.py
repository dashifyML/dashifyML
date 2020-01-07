from enum import Enum
import pandas as pd
from typing import Dict
import json

class SupportedDataTypes(Enum):
    number_type = 1
    string_type = 2
    list_type = 3
    bool_type = 4


def infer_datatypes_for_columns(df: pd.DataFrame) -> Dict[str, SupportedDataTypes]:

    def is_bool(value) -> bool:
        return str(value).lower() in ["true", "false"]

    def is_number(value) -> bool:
        try:
            float(str(value))
            return True
        except ValueError:
            return False

    def is_list(value) -> bool:
        try:
            json.loads(str(value))
            return True
        except Exception:
            return False

    def check_series(series: pd.Series, fun):
        return series.apply(fun).all()

    def infer_datatye(col_series: pd.Series):
        if check_series(col_series, is_number):
            return SupportedDataTypes.number_type
        elif check_series(col_series, is_bool):
            return SupportedDataTypes.bool_type
        elif check_series(col_series, is_list):
            return SupportedDataTypes.list_type
        else:
            return SupportedDataTypes.string_type

    cols = df.columns
    return {col: infer_datatye(df[col]) for col in cols}


def convert_string_to_supported_data_type(value: str, data_type: SupportedDataTypes):
    if data_type == SupportedDataTypes.number_type:
        return float(value)
    elif data_type == SupportedDataTypes.bool_type:
        return value.lower() == "true"
    elif data_type == SupportedDataTypes.list_type:
        return json.loads(str(value))
    else:
        return str(value)