# DataQualityApp

A Streamlit-based data quality assessment dashboard for evaluating datasets before machine learning model development.

 ## Links to streamlit apss

| Branch | URL |
|---|---|
| main | [DataQualityApp-main](https://dataqualityapp.streamlit.app/) |
| DEV | [DataQualityApp-Dev](https://dataqualityapp-dev.streamlit.app/) |

## Project Structure

```
DataQualityApp/
├── DataQualityApp.py                        # Main Streamlit entry point
├── requirements.txt
├── utils/
│   ├── data_loader.py            # CSV/Excel file loading
│   └── report_helpers.py        # Shared helper functions
└── components/
    ├── summary_stats.py          # Overview, descriptive stats, skewness flags
    ├── null_analysis.py          # Missing value counts, bar chart, heatmap
    ├── distribution.py           # Histograms, box plots, outlier detection
    ├── correlation.py            # Correlation matrix, high-corr pairs, VIF
    └── categorical.py            # Value counts, frequency charts, pie charts
```

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run DataQualityApp.py
```

Open the URL shown in your terminal (typically `http://localhost:8501`).

## Features

- **Summary Tab** — shape, dtypes, null counts, mean, median, mode, quartiles, range, IQR, skewness, kurtosis
- **Missing Values Tab** — per-column null counts and percentages, bar chart, null heatmap
- **Distributions Tab** — histogram with rug plot, box plot, IQR-based outlier summary, all-column box overview
- **Correlations Tab** — Pearson heatmap, high-correlation pair flagging (|r| > 0.8), Variance Inflation Factor (VIF) analysis
- **Categorical Tab** — distinct/unique value overview (nulls excluded from both), frequency bar charts, pie charts (≤15 categories), full value count tables

## Supported File Formats

- `.csv`
- `.xlsx`
- `.xls`
