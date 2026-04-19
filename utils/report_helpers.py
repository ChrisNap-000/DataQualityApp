import pandas as pd


def get_numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def get_categorical_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def get_datetime_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="datetime").columns.tolist()


def safe_mode(series: pd.Series):
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else None
