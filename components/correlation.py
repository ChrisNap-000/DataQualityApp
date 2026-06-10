import pandas as pd
import plotly.express as px
import streamlit as st

from utils.report_helpers import get_numeric_cols


def _compute_vif(df_numeric: pd.DataFrame) -> pd.DataFrame | None:
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor

        values = df_numeric.values
        vif_scores = []
        for i in range(values.shape[1]):
            try:
                score = variance_inflation_factor(values, i)
            except Exception:
                score = float("nan")
            vif_scores.append(round(score, 2))

        return pd.DataFrame({"Feature": df_numeric.columns, "VIF": vif_scores})
    except ImportError:
        return None


def _vif_risk_label(vif: float) -> str:
    if vif > 10:
        return "High"
    if vif > 5:
        return "Moderate"
    return "Low"


def render_correlation(df: pd.DataFrame) -> None:
    st.header("Correlation & Multicollinearity Analysis")

    num_cols = get_numeric_cols(df)
    if len(num_cols) < 2:
        st.warning("At least 2 numeric columns are required for correlation analysis.")
        return

    # Outlier filter — applied row-wise: rows outside bounds in ANY column are dropped.
    df_num = df[num_cols].copy()
    original_rows = len(df_num.dropna())

    filter_outliers = st.checkbox("Filter outliers before computing correlations")
    if filter_outliers:
        method = st.radio("Filter method", ["IQR method", "Percentile clip"], horizontal=True)
        mask = pd.Series(True, index=df_num.index)
        if method == "IQR method":
            multiplier = st.select_slider("IQR multiplier", options=[1.5, 3.0], value=1.5)
            for col in num_cols:
                col_data = df_num[col].dropna()
                Q1, Q3 = col_data.quantile(0.25), col_data.quantile(0.75)
                iqr = Q3 - Q1
                mask &= (df_num[col] >= Q1 - multiplier * iqr) & (df_num[col] <= Q3 + multiplier * iqr)
        else:
            pc1, pc2 = st.columns(2)
            lower_pct = pc1.number_input("Lower %", min_value=0.0, max_value=49.9, value=1.0, step=0.5)
            upper_pct = pc2.number_input("Upper %", min_value=50.1, max_value=100.0, value=99.0, step=0.5)
            for col in num_cols:
                col_data = df_num[col].dropna()
                mask &= (df_num[col] >= col_data.quantile(lower_pct / 100)) & \
                        (df_num[col] <= col_data.quantile(upper_pct / 100))
        df_num = df_num[mask]
        excluded = original_rows - len(df_num.dropna())
        st.caption(
            f"{excluded:,} rows excluded by outlier filter "
            f"({excluded / original_rows * 100:.1f}% of complete rows)."
        )

    corr_matrix = df_num.corr()

    fig = px.imshow(
        corr_matrix,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Correlation Matrix (Pearson)",
        aspect="auto",
    )
    fig.update_traces(textfont_size=10)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Highly Correlated Pairs (|r| > 0.8)")
    pairs = []
    for i in range(len(num_cols)):
        for j in range(i + 1, len(num_cols)):
            r = corr_matrix.iloc[i, j]
            if abs(r) > 0.8:
                pairs.append(
                    {
                        "Feature 1": num_cols[i],
                        "Feature 2": num_cols[j],
                        "Correlation": round(r, 2),
                        "Strength": "Very High (>0.9)" if abs(r) > 0.9 else "High (>0.8)",
                    }
                )

    if pairs:
        st.dataframe(pd.DataFrame(pairs), use_container_width=True, hide_index=True)
        st.warning(
            f"{len(pairs)} highly correlated pair(s) detected. "
            "Consider removing or combining redundant features before training."
        )
    else:
        st.success("No pairs with |correlation| > 0.8 found.")

    st.subheader("Variance Inflation Factor (VIF)")
    st.caption("VIF > 5: multicollinearity concern | VIF > 10: severe multicollinearity")

    df_clean = df_num.dropna()
    if len(df_clean) < 2:
        st.warning("Not enough complete rows to compute VIF.")
        return

    vif_df = _compute_vif(df_clean)
    if vif_df is None:
        st.info("Install `statsmodels` to enable VIF analysis: `pip install statsmodels`")
        return

    vif_df["Risk"] = vif_df["VIF"].apply(_vif_risk_label)
    st.dataframe(vif_df, use_container_width=True, hide_index=True)

    fig_vif = px.bar(
        vif_df.sort_values("VIF", ascending=True),
        x="VIF",
        y="Feature",
        orientation="h",
        title="Variance Inflation Factor by Feature",
        color="VIF",
        color_continuous_scale="RdYlGn_r",
    )
    fig_vif.add_vline(x=5, line_dash="dash", line_color="orange", annotation_text="VIF = 5")
    fig_vif.add_vline(x=10, line_dash="dash", line_color="red", annotation_text="VIF = 10")
    st.plotly_chart(fig_vif, use_container_width=True)
