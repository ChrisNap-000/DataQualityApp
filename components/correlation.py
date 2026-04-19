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

    corr_matrix = df[num_cols].corr()

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
                        "Correlation": round(r, 4),
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

    df_clean = df[num_cols].dropna()
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
