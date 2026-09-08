import numpy as np
import pandas as pd
import streamlit as st

from utils.report_helpers import count_unique_once, get_numeric_cols


def render_chris_tab(df: pd.DataFrame) -> None:
    st.header("Chris's Tab")

    all_cols = df.columns.tolist()
    if not all_cols:
        st.warning("No columns found.")
        return

    num_cols = set(get_numeric_cols(df))
    n_records = len(df)

    overview = pd.DataFrame(
        {
            "Column": all_cols,
            "N": [n_records for _ in all_cols],
            "Max": [df[c].max() if c in num_cols else np.nan for c in all_cols],
            "Min": [df[c].min() if c in num_cols else np.nan for c in all_cols],
            "Median": [df[c].median() if c in num_cols else np.nan for c in all_cols],
            "Range": [
                df[c].max() - df[c].min() if c in num_cols else np.nan for c in all_cols
            ],
            "Average": [df[c].mean() if c in num_cols else np.nan for c in all_cols],
            "Missing": [df[c].isnull().sum() for c in all_cols],
            "Distinct Values": [df[c].nunique() for c in all_cols],
            "Unique Values": [count_unique_once(df[c]) for c in all_cols],
        }
    )

    st.dataframe(
        overview.style.format(
            {
                "N": "{:,}",
                "Max": "{:,.2f}",
                "Min": "{:,.2f}",
                "Median": "{:,.2f}",
                "Range": "{:,.2f}",
                "Average": "{:,.2f}",
                "Missing": "{:,}",
                "Distinct Values": "{:,}",
                "Unique Values": "{:,}",
            },
            na_rep="N/A",
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(
        "Includes all column types (numeric, categorical, datetime, etc.). "
        "N = number of records in the dataset. "
        "Max, Min, Median, Range, and Average are only computed for numeric columns (shown as N/A otherwise). "
        "Distinct Values = count of distinct non-null values. "
        "Unique Values = count of non-null values that appear exactly once (a stricter definition than distinct). "
        "Missing, Distinct Values, and Unique Values all exclude null values."
    )
