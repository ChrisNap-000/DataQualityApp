import streamlit as st

from components.categorical import render_categorical
from components.correlation import render_correlation
from components.distribution import render_distributions
from components.null_analysis import render_null_analysis
from components.summary_stats import render_summary
from utils.data_loader import load_data

st.set_page_config(
    page_title="Data Quality Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("Data Quality Assessment Dashboard")
st.markdown(
    "Upload a **CSV** or **Excel** file to generate a comprehensive data quality report "
    "for machine learning readiness."
)

uploaded_file = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls"],
    help="Supported formats: CSV, XLSX, XLS",
)

if uploaded_file is not None:
    with st.spinner("Loading data..."):
        df = load_data(uploaded_file)

    if df is not None:
        st.success(
            f"Loaded **{uploaded_file.name}** — "
            f"{df.shape[0]:,} rows x {df.shape[1]} columns"
        )

        tab_summary, tab_nulls, tab_dist, tab_corr, tab_cat = st.tabs(
            ["Summary", "Missing Values", "Distributions", "Correlations", "Categorical"]
        )

        with tab_summary:
            render_summary(df)
        with tab_nulls:
            render_null_analysis(df)
        with tab_dist:
            render_distributions(df)
        with tab_corr:
            render_correlation(df)
        with tab_cat:
            render_categorical(df)
else:
    st.info("Upload a file above to get started.")
    st.markdown(
        """
        ### What this dashboard analyzes

        | Tab | What you get |
        |-----|-------------|
        | **Summary** | Shape, dtypes, null counts, mean/median/mode, quartiles, skewness, kurtosis |
        | **Missing Values** | Per-column null counts, null % bar chart, null heatmap |
        | **Distributions** | Histogram, box plot, and outlier detection (IQR) per column |
        | **Correlations** | Pearson correlation heatmap, high-correlation pair flags, VIF analysis |
        | **Categorical** | Unique value counts, frequency bar charts, pie charts |
        """
    )
