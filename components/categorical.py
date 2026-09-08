import pandas as pd
import plotly.express as px
import streamlit as st

from utils.report_helpers import count_unique_once, get_categorical_cols, safe_mode


def _case_variant_groups(series: pd.Series) -> dict[str, list[tuple[str, int]]]:
    """Return {normalized_key: [(variant, count), ...]} for groups with >1 case variant."""
    counts = series.dropna().astype(str).value_counts()
    groups: dict[str, list[tuple[str, int]]] = {}
    for value, count in counts.items():
        groups.setdefault(value.lower().strip(), []).append((value, int(count)))
    return {k: v for k, v in groups.items() if len(v) > 1}


def render_categorical(df: pd.DataFrame) -> None:
    st.header("Categorical Column Analysis")

    cat_cols = get_categorical_cols(df)
    if not cat_cols:
        st.warning("No categorical columns found.")
        return

    # Compute variant groups once; reused for Issues column and detail expander.
    all_variant_groups = {col: _case_variant_groups(df[col]) for col in cat_cols}

    def _issues_label(col: str) -> str:
        n = len(all_variant_groups[col])
        return f"⚠️ Case variants: {n} group{'s' if n != 1 else ''}" if n else ""

    overview = pd.DataFrame(
        {
            "Column": cat_cols,
            "Distinct Values": [df[c].nunique() for c in cat_cols],
            "Unique Values": [count_unique_once(df[c]) for c in cat_cols],
            "Missing": [df[c].isnull().sum() for c in cat_cols],
            "Missing %": [(df[c].isnull().sum() / len(df) * 100).round(2) for c in cat_cols],
            "Most Common": [str(safe_mode(df[c])) for c in cat_cols],
            "Most Common Count": [
                int(df[c].value_counts().iloc[0]) if not df[c].value_counts().empty else 0
                for c in cat_cols
            ],
            "Issues": [_issues_label(c) for c in cat_cols],
        }
    )

    st.subheader("Categorical Column Overview")
    st.dataframe(overview, use_container_width=True, hide_index=True)
    st.caption(
        "Distinct Values = count of distinct non-null values. "
        "Unique Values = count of values that appear exactly once (non-null). "
        "Neither column counts null values."
    )

    affected = {col: grps for col, grps in all_variant_groups.items() if grps}
    if affected:
        with st.expander(f"Case Inconsistency Detail ({len(affected)} column(s) affected)"):
            for col, groups in affected.items():
                st.markdown(f"**{col}**")
                rows = [
                    {
                        "Normalized Value": f'"{norm}"',
                        "Variants": ", ".join(
                            f"{v} × {c}"
                            for v, c in sorted(grp, key=lambda x: -x[1])
                        ),
                    }
                    for norm, grp in sorted(groups.items())
                ]
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    selected_cat = st.selectbox("Select a column to inspect", cat_cols)

    value_counts = df[selected_cat].value_counts().reset_index()
    value_counts.columns = ["Value", "Count"]
    value_counts["Percentage"] = (value_counts["Count"] / len(df) * 100).round(2)

    top_n = min(30, len(value_counts))

    fig_bar = px.bar(
        value_counts.head(top_n),
        x="Value",
        y="Count",
        title=f"Value Counts: {selected_cat} (top {top_n})",
        color="Count",
        color_continuous_scale="Blues",
        text="Percentage",
    )
    fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_bar.update_xaxes(tickangle=45)
    st.plotly_chart(fig_bar, use_container_width=True)

    if df[selected_cat].nunique() <= 15:
        fig_pie = px.pie(
            value_counts,
            names="Value",
            values="Count",
            title=f"Proportion: {selected_cat}",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader(f"Full Value Counts Table: {selected_cat}")
    st.dataframe(value_counts, use_container_width=True, hide_index=True)
