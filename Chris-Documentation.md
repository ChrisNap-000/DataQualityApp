# DataQualityApp — Developer Documentation

## Table of Contents

1. [Project Purpose](#1-project-purpose)
2. [Project Structure](#2-project-structure)
3. [Setup & Running the App](#3-setup--running-the-app)
4. [Architecture Overview](#4-architecture-overview)
5. [File-by-File Reference](#5-file-by-file-reference)
   - [app.py](#apppy)
   - [utils/data_loader.py](#utilsdata_loaderpy)
   - [utils/report_helpers.py](#utilsreport_helperspy)
   - [components/summary_stats.py](#componentssummary_statspy)
   - [components/null_analysis.py](#componentsnull_analysispy)
   - [components/distribution.py](#componentsdistributionpy)
   - [components/correlation.py](#componentscorrelationpy)
   - [components/categorical.py](#componentscategoricalpy)
6. [Dashboard Tabs](#6-dashboard-tabs)
7. [Dependencies](#7-dependencies)
8. [Data Flow](#8-data-flow)
9. [Key Concepts & Calculations](#9-key-concepts--calculations)
10. [Extending the App](#10-extending-the-app)
11. [Troubleshooting](#11-troubleshooting)
12. [Styling & Theme](#12-styling--theme)
13. [Number Formatting Standards](#13-number-formatting-standards)
14. [Changelog](#14-changelog)

---

## 1. Project Purpose

DataQualityApp is a Streamlit-based interactive dashboard that assesses the quality of a dataset (CSV or Excel) before it is used to train machine learning models. It produces a visual report covering descriptive statistics, missing values, distributions, correlations, multicollinearity, and categorical breakdowns — all without writing a single line of analysis code by hand.

**Primary use case:** Upload a raw dataset, identify data quality issues, and decide what cleaning or transformation steps are needed before modeling.

---

## 2. Project Structure

```
DataQualityApp/
├── app.py                        # Entry point — Streamlit page config, file uploader, tab routing
├── requirements.txt              # Python dependency list
├── documentation.md              # This file
├── README.md                     # Quick-start guide
│
├── utils/                        # Shared utilities (no Streamlit rendering)
│   ├── __init__.py
│   ├── data_loader.py            # Reads uploaded CSV/Excel files into a DataFrame
│   └── report_helpers.py        # Column-type detection and other shared helpers
│
└── components/                   # One file per dashboard tab (Streamlit rendering)
    ├── __init__.py
    ├── summary_stats.py          # Tab: Summary
    ├── null_analysis.py          # Tab: Missing Values
    ├── distribution.py           # Tab: Distributions
    ├── correlation.py            # Tab: Correlations
    └── categorical.py            # Tab: Categorical
```

**Design principle:** `utils/` contains pure logic (no Streamlit calls). `components/` contains rendering logic (calls `st.*` and calls into `utils/`). `app.py` only wires everything together. This separation makes each file easy to test, debug, and extend independently.

---

## 3. Setup & Running the App

### Install dependencies

```bash
pip install -r requirements.txt
```

### Launch the app

```bash
streamlit run app.py
```

Streamlit will open a browser tab at `http://localhost:8501` by default.

### Supported file formats

| Format | Extension | Engine used |
|--------|-----------|-------------|
| CSV | `.csv` | pandas built-in |
| Excel (modern) | `.xlsx` | openpyxl |
| Excel (legacy) | `.xls` | xlrd |

---

## 4. Architecture Overview

```
User uploads file
       |
       v
  app.py  ──► load_data()          (utils/data_loader.py)
       |              |
       |        pd.DataFrame
       |              |
       v              v
  st.tabs()   ──► render_*(df)     (components/*.py)
                       |
                 report_helpers     (utils/report_helpers.py)
                       |
                  plotly figures + st.dataframe()
```

**Control flow:**

1. `app.py` renders the file uploader.
2. When a file is uploaded, `load_data()` parses it and returns a `pd.DataFrame`.
3. `app.py` creates five tabs and calls the matching `render_*` function from `components/` for each tab, passing the same DataFrame to all of them.
4. Each component independently queries the DataFrame using helpers from `utils/report_helpers.py` and renders its section using Streamlit and Plotly.

No global state is shared between components — each `render_*` function is fully self-contained.

---

## 5. File-by-File Reference

### app.py

**Role:** Entry point. Owns page configuration, file upload, and tab routing.

**Key logic:**
- `st.set_page_config(layout="wide")` — forces wide layout for better chart visibility.
- `st.file_uploader(type=["csv", "xlsx", "xls"])` — restricts accepted file types at the browser level.
- Calls `load_data()` inside `st.spinner()` to give the user visual feedback during large file reads.
- Uses `st.tabs()` to split the report into five named sections.
- When no file is uploaded, renders a landing page table summarizing what each tab provides.

**Dependencies used:** `streamlit`, all five `components/` modules, `utils.data_loader`

---

### utils/data_loader.py

**Role:** Safely reads a Streamlit `UploadedFile` object into a `pd.DataFrame`.

**Function:**

```python
load_data(uploaded_file) -> pd.DataFrame | None
```

**Behavior:**
- Detects file type from the filename extension (`.csv`, `.xlsx`, `.xls`).
- Uses the correct pandas engine per format (`openpyxl` for `.xlsx`, `xlrd` for `.xls`).
- Returns `None` and displays a Streamlit error/warning if the file cannot be parsed or is empty.
- Wraps everything in a `try/except` so a malformed file never crashes the app.

**Error states handled:**

| Situation | User sees |
|-----------|-----------|
| Unsupported extension | `st.error` |
| File is empty | `st.warning` |
| Parse exception | `st.error` with the exception message |

---

### utils/report_helpers.py

**Role:** Shared, stateless helper functions used by multiple components.

**Functions:**

| Function | Returns | Description |
|----------|---------|-------------|
| `get_numeric_cols(df)` | `list[str]` | Columns with numeric dtypes (`int`, `float`, etc.) |
| `get_categorical_cols(df)` | `list[str]` | Columns with `object` or `category` dtypes |
| `get_datetime_cols(df)` | `list[str]` | Columns with datetime dtypes |
| `safe_mode(series)` | scalar or `None` | Returns the first mode of a Series, or `None` if the Series is all-null |

**Why `safe_mode` exists:** `pd.Series.mode()` returns an empty Series when all values are NaN, causing an `IndexError` if you do `.iloc[0]` directly. `safe_mode` guards against this.

---

### components/summary_stats.py

**Role:** Renders the **Summary** tab — the first and broadest view of the dataset.

**Public function:**

```python
render_summary(df: pd.DataFrame) -> None
```

**What it renders:**

1. **Four top-level metrics** — row count, column count, numeric column count, categorical column count.

2. **Column Info table** — one row per column, showing:
   - Data type (`dtype`)
   - Null count and null percentage
   - Unique value count and unique percentage

3. **Numeric Statistics table** — for all numeric columns, showing:
   - Count, Mean, Std Dev, Min, Q1, Median, Q3, Max (from `describe()`)
   - Range (`Max - Min`)
   - IQR (`Q3 - Q1`)
   - Skewness and Kurtosis (from pandas `.skew()` / `.kurt()`)
   - Mode (via `safe_mode()`)

4. **Skewness warning** — if any column has `|skewness| >= 1`, a yellow warning banner lists those columns with their skew values and recommends a transformation.

5. **Data Preview** — the first 10 rows of the raw DataFrame.

**Private function:**

```python
_render_skewness_flags(df, num_cols) -> None
```

Isolated so the skewness check logic can be updated or tested independently from the main render function.

---

### components/null_analysis.py

**Role:** Renders the **Missing Values** tab.

**Public function:**

```python
render_null_analysis(df: pd.DataFrame) -> None
```

**What it renders:**

1. **Three top-level metrics** — total missing cells, overall missing percentage across all cells, number of columns that have at least one null.

2. **Missing Values by Column table** — sorted descending by missing count, showing count, percentage, and present count per column.

3. **Bar chart** — missing value percentage per column, only for columns that have at least one null. Uses a red color scale (darker = more missing).

4. **Null Heatmap** — a matrix where:
   - Rows = individual data rows (sampled to 300 if the dataset is large)
   - Columns = only columns that have at least one null
   - Dark red = missing, light blue = present
   - Built using `plotly.express.imshow` on a boolean mask cast to integers

**Performance note:** The heatmap is capped at 300 rows via random sampling to prevent the chart from becoming unreadable or slow on large datasets.

**Early return:** If no nulls exist at all, renders a success message and stops — no charts are shown for a clean dataset.

---

### components/distribution.py

**Role:** Renders the **Distributions** tab for numeric columns.

**Public function:**

```python
render_distributions(df: pd.DataFrame) -> None
```

**What it renders:**

1. **Column selector** — dropdown (`st.selectbox`) to pick which numeric column to inspect.

2. **Four quick metrics** — Mean, Median, Std Dev, Skewness for the selected column.

3. **Histogram** (left column) — 50-bin histogram with a rug plot on the margin. Blue color scheme.

4. **Box Plot** (right column) — standard box-and-whisker with outlier points overlaid. Green color scheme.

5. **Outlier Summary** — computed using the IQR method:
   - Lower fence = Q1 − 1.5 × IQR
   - Upper fence = Q3 + 1.5 × IQR
   - Any point outside these fences is counted as an outlier
   - Shows outlier count, outlier percentage, and IQR value

6. **All-columns box plot** — a single chart with one box per numeric column, allowing quick visual comparison of spread and center across all numeric features. Uses `pd.DataFrame.melt()` to reshape the data for Plotly.

**Private function:**

```python
_render_outlier_summary(col_data: pd.Series, col_name: str) -> None
```

Contains the IQR fence math and metric display, separated from the main render function for clarity.

---

### components/correlation.py

**Role:** Renders the **Correlations** tab — identifies linear relationships and multicollinearity between numeric features.

**Public function:**

```python
render_correlation(df: pd.DataFrame) -> None
```

**What it renders:**

1. **Pearson Correlation Heatmap** — a full matrix heatmap with values annotated inside each cell. Uses a diverging red-blue color scale (red = strong positive, blue = strong negative, white = no correlation). Built with `plotly.express.imshow`.

2. **Highly Correlated Pairs table** — iterates over the upper triangle of the correlation matrix and collects all pairs where `|r| > 0.8`. Displays a table with columns: Feature 1, Feature 2, Correlation value, and Strength label (High or Very High). If any pairs are found, a warning banner prompts the user to consider removing redundant features.

3. **Variance Inflation Factor (VIF) table** — computes VIF for each numeric feature using `statsmodels`. Each feature gets a Risk label:
   - Low: VIF <= 5
   - Moderate: 5 < VIF <= 10
   - High: VIF > 10

4. **VIF bar chart** — horizontal bar chart of VIF values, color-coded from green (low) to red (high). Reference lines at VIF = 5 (orange, dashed) and VIF = 10 (red, dashed).

**Private functions:**

```python
_compute_vif(df_numeric: pd.DataFrame) -> pd.DataFrame | None
```
Wraps the `statsmodels` VIF call with per-feature exception handling. Returns `None` if `statsmodels` is not installed, allowing the app to degrade gracefully without crashing.

```python
_vif_risk_label(vif: float) -> str
```
Converts a VIF score to a human-readable risk label string.

**Multicollinearity explained:** VIF measures how much the variance of a regression coefficient is inflated due to correlation with other features. A VIF of 1 means no correlation. A VIF > 10 means the feature's coefficient estimate is unreliable and the feature may be redundant.

---

### components/categorical.py

**Role:** Renders the **Categorical** tab for string/category columns.

**Public function:**

```python
render_categorical(df: pd.DataFrame) -> None
```

**What it renders:**

1. **Categorical Column Overview table** — one row per categorical column, showing:
   - Unique value count
   - Missing count and percentage
   - Most common value (the mode)
   - Count of the most common value

2. **Column selector** — dropdown to pick which categorical column to deep-dive.

3. **Bar chart** — top 30 values by frequency for the selected column. Bars are labeled with their percentage of the total. Uses a blue color scale.

4. **Pie chart** — shown only when the column has 15 or fewer unique values. Provides a proportion view of the category split.

5. **Full Value Counts table** — the complete sorted value counts with count and percentage columns.

**Design note:** The pie chart is conditionally shown. With more than 15 slices, pie charts become unreadable, so a bar chart alone is used for high-cardinality columns.

---

## 6. Dashboard Tabs

| Tab | Component File | Primary Audience Question |
|-----|---------------|--------------------------|
| Summary | `summary_stats.py` | What does my data look like overall? |
| Missing Values | `null_analysis.py` | Where is data missing, and how much? |
| Distributions | `distribution.py` | How are my numeric features shaped? Are there outliers? |
| Correlations | `correlation.py` | Are features linearly related? Is there multicollinearity? |
| Categorical | `categorical.py` | What are the unique categories and how common are they? |

---

## 7. Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | >=1.30.0 | Web app framework and UI components |
| `pandas` | >=2.0.0 | DataFrame manipulation and statistics |
| `numpy` | >=1.24.0 | Numeric operations |
| `plotly` | >=5.18.0 | Interactive charts (heatmaps, histograms, box plots, bars, pie) |
| `openpyxl` | >=3.1.0 | Reading `.xlsx` files |
| `xlrd` | >=2.0.1 | Reading legacy `.xls` files |
| `statsmodels` | >=0.14.0 | Variance Inflation Factor (VIF) computation |
| `scipy` | >=1.11.0 | Statistical functions (available for future extensions) |

**Note on `statsmodels`:** The VIF section in the Correlations tab degrades gracefully — if `statsmodels` is not installed, a message is shown instead of crashing the app.

---

## 8. Data Flow

```
UploadedFile (Streamlit)
        |
        v
load_data()                      # utils/data_loader.py
        |
        v
pd.DataFrame
        |
        +---> render_summary()         # components/summary_stats.py
        |           |
        |     get_numeric_cols()       # utils/report_helpers.py
        |     get_categorical_cols()
        |     safe_mode()
        |
        +---> render_null_analysis()   # components/null_analysis.py
        |
        +---> render_distributions()   # components/distribution.py
        |           |
        |     get_numeric_cols()
        |
        +---> render_correlation()     # components/correlation.py
        |           |
        |     get_numeric_cols()
        |     _compute_vif()
        |
        +---> render_categorical()     # components/categorical.py
                    |
              get_categorical_cols()
              safe_mode()
```

The DataFrame is read once and passed by reference to all components — no copies are made, and no component modifies it.

---

## 9. Key Concepts & Calculations

### Skewness
Measures asymmetry of a distribution. Computed via `pd.Series.skew()`.
- `|skew| < 0.5` — fairly symmetric
- `0.5 <= |skew| < 1` — moderate skew
- `|skew| >= 1` — high skew; the app flags these columns with a warning

### IQR Outlier Detection
The Interquartile Range method defines outliers as points outside the "fences":
```
Lower fence = Q1 - (1.5 × IQR)
Upper fence = Q3 + (1.5 × IQR)
IQR = Q3 - Q1
```
This is the same method used by standard box plots. A data point beyond either fence is counted as an outlier.

### Pearson Correlation
Measures the linear relationship between two numeric variables. Values range from -1 (perfect negative) to +1 (perfect positive). Computed via `pd.DataFrame.corr()`.

### Variance Inflation Factor (VIF)
Quantifies how much a feature's regression coefficient variance is inflated by its correlation with other features.
```
VIF_i = 1 / (1 - R²_i)
```
where `R²_i` is the R-squared from regressing feature `i` on all other features.
- VIF = 1: no multicollinearity
- VIF > 5: concern — the feature shares substantial variance with others
- VIF > 10: severe — the feature may be a near-linear combination of others

---

## 10. Extending the App

### Adding a new tab

1. Create a new file in `components/`, e.g., `components/datetime_analysis.py`.
2. Define a `render_datetime_analysis(df: pd.DataFrame) -> None` function inside it.
3. In `app.py`, import the function and add a new tab:
   ```python
   from components.datetime_analysis import render_datetime_analysis
   
   # Add "Datetime" to the st.tabs() call
   tab_dt = st.tabs([..., "Datetime"])
   with tab_dt:
       render_datetime_analysis(df)
   ```

### Adding a new helper

Add the function to `utils/report_helpers.py` and import it in the component that needs it. Keep helpers stateless (no `st.*` calls).

### Adding a new statistic to the Summary tab

Extend the `desc` DataFrame in `render_summary()` inside [components/summary_stats.py](components/summary_stats.py) before the `st.dataframe()` call. For example, to add a coefficient of variation:
```python
desc["CV %"] = (desc["Std Dev"] / desc["Mean"].abs() * 100).round(2)
```

---

## 11. Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: statsmodels` | `statsmodels` not installed | Run `pip install statsmodels` |
| `ModuleNotFoundError: openpyxl` | Missing Excel engine | Run `pip install openpyxl` |
| App loads but charts are blank | Column has all-null values | Check the null analysis tab first |
| VIF shows `NaN` for a feature | Perfect multicollinearity or singular matrix | That feature is a linear combination of others — remove it |
| Heatmap is slow | Dataset has many columns or rows | The heatmap is capped at 300 rows; consider reducing columns before uploading |
| `KeyError` on a column name | Column name has leading/trailing whitespace | Strip column names before uploading: `df.columns = df.columns.str.strip()` |

---

## 12. Styling & Theme

The app uses a custom Streamlit theme defined in `.streamlit/config.toml`.

```toml
[theme]
primaryColor = "#00BCD4"          # Electric teal — used for selected tabs, buttons, sliders
backgroundColor = "#0F1117"       # Near-black with a subtle blue tint
secondaryBackgroundColor = "#1E2130"  # Dark navy — used for sidebar and widget backgrounds
textColor = "#E2E8F0"             # Soft white
font = "sans serif"

[browser]
gatherUsageStats = false
```

**Page config** is set in `DataQualityApp.py`:

```python
st.set_page_config(
    page_title="Data Quality Dashboard",
    page_icon="📊",
    layout="wide",
)
```

**Note:** If the tab selection or interactive element color appears red after editing `config.toml`, the Streamlit server must be fully restarted (`Ctrl+C`, then `streamlit run DataQualityApp.py`) for the theme to take effect. The red is Streamlit's built-in default (`#FF4B4B`) and is replaced on restart.

---

## 13. Number Formatting Standards

All numeric values displayed in the app follow these formatting rules:

| Value type | Format spec | Example output |
|---|---|---|
| Decimal values (general) | `:,.2f` | `1,234.56` |
| Percentages | `:.2f%` | `12.34%` |
| Integer counts | `:,` | `1,234,567` |
| Correlations | `round(r, 2)` | `0.87` (no thousands — always < 1) |

**Thousands separators** (`,`) are applied to all values that can exceed 999 — including means, standard deviations, IQR, fence values, and the numeric statistics table. Percentages and correlations are excluded since they never exceed three digits.

**Files where formatting is applied:**

| File | Formatted values |
|---|---|
| `components/distribution.py` | Mean, Median, Std Dev, Skewness, IQR, Lower/Upper fence |
| `components/summary_stats.py` | Entire numeric stats table, skewness warning values |
| `components/null_analysis.py` | Overall Missing % metric, bar chart labels |
| `components/categorical.py` | Bar chart percentage labels |
| `components/correlation.py` | Correlated pairs table |

---

## 14. Changelog

### 2026-04-22

**Dark theme & branding**
- Created `.streamlit/config.toml` with a dark theme: near-black background (`#0F1117`), dark navy sidebar (`#1E2130`), electric teal accent (`#00BCD4`), soft white text (`#E2E8F0`).
- Added `page_icon="📊"` to `st.set_page_config()` in `DataQualityApp.py`.
- Set `page_title` to `"Data Quality Dashboard"`.

**Number formatting — 2 decimal places**
- `distribution.py`: IQR and lower/upper fence values changed from `:.4f` to `:.2f`.
- `summary_stats.py`: Numeric statistics table changed from `{:.4f}` to `{:.2f}`.
- `null_analysis.py`: Bar chart labels changed from `:.1f%` to `:.2f%`.
- `categorical.py`: Bar chart labels changed from `:.1f%` to `:.2f%`.
- `correlation.py`: Highly correlated pairs table changed from `round(r, 4)` to `round(r, 2)`.

**Number formatting — thousands separators**
- `distribution.py`: Mean, Median, Std Dev, Skewness metrics updated to `:,.2f`. IQR and fence values updated to `:,.2f`.
- `summary_stats.py`: Numeric statistics table updated to `{:,.2f}`. Skewness warning values updated to `:,.2f`.
- `null_analysis.py`: Bar chart labels updated to `:.2f%` (percentages excluded from thousands separator).
- `categorical.py`: Bar chart labels updated to `:.2f%` (percentages excluded from thousands separator).
