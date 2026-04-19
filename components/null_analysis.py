import pandas as pd
import plotly.express as px
import streamlit as st


def render_null_analysis(df: pd.DataFrame) -> None:
    st.header("Missing Value Analysis")

    null_counts = df.isnull().sum()
    null_pct = (null_counts / len(df) * 100).round(2)
    total_nulls = int(null_counts.sum())
    total_cells = df.shape[0] * df.shape[1]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Missing Cells", f"{total_nulls:,}")
    c2.metric("Overall Missing %", f"{total_nulls / total_cells * 100:.2f}%")
    c3.metric("Columns with Missing Data", int((null_counts > 0).sum()))

    null_df = (
        pd.DataFrame(
            {
                "Column": null_counts.index,
                "Missing Count": null_counts.values,
                "Missing %": null_pct.values,
                "Present Count": (len(df) - null_counts).values,
            }
        )
        .sort_values("Missing Count", ascending=False)
        .reset_index(drop=True)
    )

    st.subheader("Missing Values by Column")
    st.dataframe(null_df, use_container_width=True, hide_index=True)

    cols_with_nulls = null_df[null_df["Missing Count"] > 0]

    if cols_with_nulls.empty:
        st.success("No missing values found in this dataset.")
        return

    fig_bar = px.bar(
        cols_with_nulls,
        x="Column",
        y="Missing %",
        title="Missing Value % by Column",
        color="Missing %",
        color_continuous_scale="Reds",
        text="Missing %",
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Null Value Heatmap")
    st.caption("Dark = Missing, Light = Present")

    cols_to_show = cols_with_nulls["Column"].tolist()
    null_mask = df[cols_to_show].isnull().astype(int)

    max_rows = 300
    if len(null_mask) > max_rows:
        null_mask = null_mask.sample(max_rows, random_state=42).reset_index(drop=True)
        st.caption(f"Showing a random sample of {max_rows} rows for the heatmap.")

    fig_heat = px.imshow(
        null_mask.T,
        color_continuous_scale=["#dbeafe", "#dc2626"],
        title="Null Heatmap (only columns with missing data shown)",
        labels={"color": "Missing"},
        aspect="auto",
    )
    fig_heat.update_coloraxes(showscale=False)
    st.plotly_chart(fig_heat, use_container_width=True)
