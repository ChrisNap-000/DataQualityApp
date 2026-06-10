import pandas as pd


def get_numeric_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="number").columns.tolist()


def get_categorical_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include=["object", "category"]).columns.tolist()


def get_datetime_cols(df: pd.DataFrame) -> list[str]:
    return df.select_dtypes(include="datetime").columns.tolist()


def safe_mode(series: pd.Series):
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else None


def get_data_warnings(df: pd.DataFrame) -> list[dict]:
    warnings: list[dict] = []

    for col in df.select_dtypes(include="number").columns:
        col_data = df[col].dropna()
        if col_data.empty:
            continue

        # (a) Sentinel/garbage value: max far above mean
        mean, std, max_val = col_data.mean(), col_data.std(), col_data.max()
        if std and max_val > mean + 10 * std:
            warnings.append({
                "check": "sentinel",
                "severity": "high",
                "column": col,
                "message": f"max={max_val:.0f} is far above mean={mean:.0f}",
            })

        # (d) Extreme skew
        skew = col_data.skew()
        if abs(skew) > 10:
            warnings.append({
                "check": "skew",
                "severity": "medium",
                "column": col,
                "message": f"skewness = {skew:.1f}",
            })

    for col in df.select_dtypes(include=["object", "category"]).columns:
        # (b) Case inconsistency: collect every group that has multiple case variants
        values = df[col].dropna().astype(str).unique()
        groups: dict[str, list[str]] = {}
        for v in values:
            groups.setdefault(v.lower().strip(), []).append(v)
        inconsistent = [sorted(variants) for variants in groups.values() if len(variants) > 1]
        if inconsistent:
            group_strs = [" / ".join(repr(v) for v in g) for g in inconsistent]
            warnings.append({
                "check": "case",
                "severity": "medium",
                "column": col,
                "message": ", ".join(group_strs),
            })

    # (c) High missingness across all columns
    for col in df.columns:
        null_pct = df[col].isna().mean() * 100
        if null_pct > 15:
            warnings.append({
                "check": "missing",
                "severity": "medium",
                "column": col,
                "message": f"{null_pct:.1f}% null",
            })

    return warnings
