# DataQualityApp

A Streamlit-based data quality assessment dashboard for evaluating datasets before machine learning model development.

## Project Structure

```
DataQualityApp/
├── app.py                        # Main Streamlit entry point
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
streamlit run app.py
```

Open the URL shown in your terminal (typically `http://localhost:8501`).

## Features

- **Summary Tab** — shape, dtypes, null counts, mean, median, mode, quartiles, range, IQR, skewness, kurtosis
- **Missing Values Tab** — per-column null counts and percentages, bar chart, null heatmap
- **Distributions Tab** — histogram with rug plot, box plot, IQR-based outlier summary, all-column box overview
- **Correlations Tab** — Pearson heatmap, high-correlation pair flagging (|r| > 0.8), Variance Inflation Factor (VIF) analysis
- **Categorical Tab** — unique value overview, frequency bar charts, pie charts (≤15 categories), full value count tables

## Supported File Formats

- `.csv`
- `.xlsx`
- `.xls`
