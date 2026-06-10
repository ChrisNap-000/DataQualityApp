import pandas as pd
import streamlit as st

from utils.report_helpers import get_categorical_cols, get_data_warnings, get_numeric_cols, safe_mode


def render_summary(df: pd.DataFrame) -> None:
    st.header("Dataset Overview")

    num_cols = get_numeric_cols(df)
    cat_cols = get_categorical_cols(df)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{df.shape[0]:,}")
    c2.metric("Columns", df.shape[1])
    c3.metric("Numeric Columns", len(num_cols))
    c4.metric("Categorical Columns", len(cat_cols))

    st.subheader("Column Info")
    info = pd.DataFrame(
        {
            "Column": df.columns,
            "Dtype": [str(d) for d in df.dtypes.values],
            "Nulls": df.isnull().sum().values,
            "Null %": (df.isnull().sum().values / len(df) * 100).round(2),
            "Unique Values": df.nunique().values,
            "Unique %": (df.nunique().values / len(df) * 100).round(2),
        }
    )
    st.dataframe(info, use_container_width=True, hide_index=True)

    st.subheader("Data Quality Warnings")
    dq_warnings = get_data_warnings(df)
    if not dq_warnings:
        st.success("No data quality warnings detected.")
    else:
        # Group by check type; render one tab per type that has warnings.
        _TAB_ORDER = [
            ("sentinel", "⚠️ Sentinel Values"),
            ("case",     "⚠️ Case Inconsistency"),
            ("missing",  "⚠️ High Missingness"),
            ("skew",     "⚠️ Extreme Skew"),
        ]
        grouped: dict[str, list[dict]] = {}
        for w in dq_warnings:
            grouped.setdefault(w["check"], []).append(w)

        active = [(key, label) for key, label in _TAB_ORDER if key in grouped]
        tabs = st.tabs([label for _, label in active])

        for tab, (key, _) in zip(tabs, active):
            with tab:
                entries = grouped[key]
                if key == "sentinel":
                    cols_detail = ", ".join(
                        f"**{e['column']}** ({e['message']})" for e in entries
                    )
                    st.error(f"Dataset contains extreme outliers in Column(s): {cols_detail}")
                elif key == "case":
                    cols_detail = ", ".join(f"**{e['column']}**" for e in entries)
                    st.warning(f"Case inconsistencies detected in Column(s): {cols_detail}")
                    for e in entries:
                        st.caption(f"  {e['column']}: {e['message']}")
                elif key == "missing":
                    cols_detail = ", ".join(
                        f"**{e['column']}** ({e['message']})" for e in entries
                    )
                    st.warning(f"High missingness (>15%) in Column(s): {cols_detail}")
                else:  # skew
                    cols_detail = ", ".join(
                        f"**{e['column']}** ({e['message']})" for e in entries
                    )
                    st.warning(f"Extreme skewness (|skew| > 10) in Column(s): {cols_detail}")

    if num_cols:
        st.subheader("Numeric Statistics")
        desc = df[num_cols].describe(percentiles=[0.25, 0.5, 0.75]).T
        desc.columns = ["Count", "Mean", "Std Dev", "Min", "Q1", "Median", "Q3", "Max"]
        desc["Range"] = desc["Max"] - desc["Min"]
        desc["IQR"] = desc["Q3"] - desc["Q1"]
        desc["Skewness"] = df[num_cols].skew()
        desc["Kurtosis"] = df[num_cols].kurt()
        desc["Mode"] = [safe_mode(df[c]) for c in num_cols]
        st.dataframe(desc.style.format("{:,.2f}", na_rep="N/A"), use_container_width=True)

        _render_skewness_flags(df, num_cols)

    st.subheader("Data Preview (first 10 rows)")
    st.dataframe(df.head(10), use_container_width=True)


def _render_skewness_flags(df: pd.DataFrame, num_cols: list[str]) -> None:
    skew = df[num_cols].skew().abs()
    high_skew = skew[skew >= 1].sort_values(ascending=False)
    if not high_skew.empty:
        st.warning(
            f"**{len(high_skew)} column(s) have high skewness (|skew| >= 1):** "
            + ", ".join(f"`{c}` ({v:,.2f})" for c, v in high_skew.items())
            + ". Consider transformations before modeling."
        )
