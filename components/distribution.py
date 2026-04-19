import pandas as pd
import plotly.express as px
import streamlit as st

from utils.report_helpers import get_numeric_cols


def render_distributions(df: pd.DataFrame) -> None:
    st.header("Numeric Column Distributions")

    num_cols = get_numeric_cols(df)
    if not num_cols:
        st.warning("No numeric columns found.")
        return

    selected_col = st.selectbox("Select a column to inspect", num_cols)

    col_data = df[selected_col].dropna()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mean", f"{col_data.mean():.4f}")
    m2.metric("Median", f"{col_data.median():.4f}")
    m3.metric("Std Dev", f"{col_data.std():.4f}")
    m4.metric("Skewness", f"{col_data.skew():.4f}")

    left, right = st.columns(2)
    with left:
        fig_hist = px.histogram(
            df,
            x=selected_col,
            title=f"Histogram: {selected_col}",
            marginal="rug",
            nbins=50,
            color_discrete_sequence=["#3b82f6"],
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with right:
        fig_box = px.box(
            df,
            y=selected_col,
            title=f"Box Plot: {selected_col}",
            color_discrete_sequence=["#10b981"],
            points="outliers",
        )
        st.plotly_chart(fig_box, use_container_width=True)

    _render_outlier_summary(col_data, selected_col)

    st.subheader("All Numeric Columns — Box Plot Overview")
    melted = df[num_cols].melt(var_name="Column", value_name="Value")
    fig_all = px.box(
        melted,
        x="Column",
        y="Value",
        title="Distribution Overview (all numeric columns)",
        points=False,
    )
    fig_all.update_xaxes(tickangle=45)
    st.plotly_chart(fig_all, use_container_width=True)


def _render_outlier_summary(col_data: pd.Series, col_name: str) -> None:
    Q1 = col_data.quantile(0.25)
    Q3 = col_data.quantile(0.75)
    IQR = Q3 - Q1
    lower_fence = Q1 - 1.5 * IQR
    upper_fence = Q3 + 1.5 * IQR
    outliers = col_data[(col_data < lower_fence) | (col_data > upper_fence)]

    st.subheader(f"Outlier Summary — {col_name} (IQR Method)")
    o1, o2, o3 = st.columns(3)
    o1.metric("Outlier Count", len(outliers))
    o2.metric("Outlier %", f"{len(outliers) / len(col_data) * 100:.2f}%")
    o3.metric("IQR", f"{IQR:.4f}")
    st.caption(f"Lower fence: {lower_fence:.4f}  |  Upper fence: {upper_fence:.4f}")
