# ============================================================
# DataMind AI - Data Cleaning Module
# ============================================================

import numpy as np
import pandas as pd


# ============================================================
# HELPER
# ============================================================

def _safe_dataframe(df):
    """
    Validate that the input is a pandas DataFrame.
    """

    if df is None:
        raise ValueError("DataFrame cannot be None.")

    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    return df


# ============================================================
# DATA QUALITY
# ============================================================

def get_data_quality(df):
    """
    Calculate overall data-quality metrics.

    Returns:
        dict containing:
        - rows
        - columns
        - missing_values
        - missing_percentage
        - duplicate_rows
        - duplicate_percentage
        - quality_score
    """

    if df is None or not isinstance(df, pd.DataFrame):
        return {
            "rows": 0,
            "columns": 0,
            "missing_values": 0,
            "missing_percentage": 0.0,
            "duplicate_rows": 0,
            "duplicate_percentage": 0.0,
            "quality_score": 100.0,
        }

    rows = len(df)
    columns = len(df.columns)

    # --------------------------------------------------------
    # Empty DataFrame
    # --------------------------------------------------------

    if rows == 0 or columns == 0:
        return {
            "rows": rows,
            "columns": columns,
            "missing_values": 0,
            "missing_percentage": 0.0,
            "duplicate_rows": 0,
            "duplicate_percentage": 0.0,
            "quality_score": 100.0,
        }

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    total_cells = rows * columns

    missing_values = int(
        df.isna().sum().sum()
    )

    missing_percentage = (
        missing_values / total_cells
    ) * 100

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    duplicate_rows = int(
        df.duplicated().sum()
    )

    duplicate_percentage = (
        duplicate_rows / rows
    ) * 100

    # --------------------------------------------------------
    # Quality score
    # --------------------------------------------------------

    quality_score = (
        100
        - (missing_percentage * 0.7)
        - (duplicate_percentage * 0.3)
    )

    quality_score = max(
        0,
        min(
            100,
            round(quality_score, 1)
        )
    )

    return {
        "rows": rows,
        "columns": columns,
        "missing_values": missing_values,
        "missing_percentage": round(
            missing_percentage,
            2
        ),
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": round(
            duplicate_percentage,
            2
        ),
        "quality_score": quality_score,
    }


# ============================================================
# DETAILED DATA QUALITY SCAN
# ============================================================

def scan_data_quality(df):
    """
    Perform a detailed data-quality scan.

    Detects:
    - Missing values
    - Duplicate rows
    - Numerical outliers
    - Possible invalid dates

    Returns:
        list of dictionaries
    """

    df = _safe_dataframe(df)

    issues = []

    if df.empty:
        return issues

    # ========================================================
    # MISSING VALUES
    # ========================================================

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        if missing_count > 0:

            percentage = round(
                missing_count / len(df) * 100,
                2
            )

            issues.append({
                "type": "Missing Values",
                "column": str(column),
                "count": missing_count,
                "percentage": percentage,
            })

    # ========================================================
    # DUPLICATE ROWS
    # ========================================================

    duplicate_count = int(
        df.duplicated().sum()
    )

    if duplicate_count > 0:

        issues.append({
            "type": "Duplicate Rows",
            "column": "All Columns",
            "count": duplicate_count,
            "percentage": round(
                duplicate_count / len(df) * 100,
                2
            ),
        })

    # ========================================================
    # OUTLIERS USING IQR
    # ========================================================

    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns

    for column in numeric_columns:

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)

        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = (
            q1 - 1.5 * iqr
        )

        upper_bound = (
            q3 + 1.5 * iqr
        )

        outlier_count = int(
            (
                (series < lower_bound)
                |
                (series > upper_bound)
            ).sum()
        )

        if outlier_count > 0:

            issues.append({
                "type": "Outliers",
                "column": str(column),
                "count": outlier_count,
                "percentage": round(
                    outlier_count / len(series) * 100,
                    2
                ),
            })

    # ========================================================
    # POSSIBLE INVALID DATES
    # ========================================================

    for column in df.columns:

        # Skip numerical columns
        if pd.api.types.is_numeric_dtype(
            df[column]
        ):
            continue

        non_null = df[column].dropna()

        if non_null.empty:
            continue

        converted = pd.to_datetime(
            non_null,
            errors="coerce"
        )

        valid_ratio = converted.notna().mean()

        # Consider a column date-like when
        # at least 80% of values can be converted.
        if valid_ratio >= 0.80:

            invalid_count = int(
                converted.isna().sum()
            )

            if invalid_count > 0:

                issues.append({
                    "type": "Invalid Dates",
                    "column": str(column),
                    "count": invalid_count,
                    "percentage": round(
                        invalid_count / len(non_null) * 100,
                        2
                    ),
                })

    return issues


# ============================================================
# FILL NUMERICAL MISSING VALUES
# ============================================================

def fill_missing_numeric(
    df,
    column,
    strategy="median"
):
    """
    Fill missing numerical values.

    Strategies:
    - mean
    - median
    - zero
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    if column not in cleaned_df.columns:
        return cleaned_df

    series = pd.to_numeric(
        cleaned_df[column],
        errors="coerce"
    )

    strategy = str(strategy).lower()

    if strategy == "mean":

        value = series.mean()

    elif strategy == "median":

        value = series.median()

    elif strategy == "zero":

        value = 0

    else:

        value = series.median()

    if pd.notna(value):

        cleaned_df[column] = (
            series.fillna(value)
        )

    return cleaned_df


# ============================================================
# FILL CATEGORICAL MISSING VALUES
# ============================================================

def fill_missing_categorical(
    df,
    column
):
    """
    Fill missing categorical values
    using the most frequent value.
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    if column not in cleaned_df.columns:
        return cleaned_df

    mode_values = cleaned_df[column].mode(
        dropna=True
    )

    if not mode_values.empty:

        mode_value = mode_values.iloc[0]

        cleaned_df[column] = (
            cleaned_df[column]
            .fillna(mode_value)
        )

    else:

        cleaned_df[column] = (
            cleaned_df[column]
            .fillna("Unknown")
        )

    return cleaned_df


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):
    """
    Remove exact duplicate rows.

    This is the function used by data_analyst.py.
    """

    df = _safe_dataframe(df)

    return (
        df.copy()
        .drop_duplicates()
        .reset_index(drop=True)
    )


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def remove_duplicate_rows(df):
    """
    Alias for remove_duplicates().

    Kept for compatibility with older code.
    """

    return remove_duplicates(df)


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

def handle_missing_values(
    df,
    method
):
    """
    Handle missing values.

    Supported methods:
    - Do Nothing
    - Drop Rows
    - Mean
    - Median
    - Mode
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    if method == "Do Nothing":

        return cleaned_df

    # ========================================================
    # DROP ROWS
    # ========================================================

    elif method == "Drop Rows":

        return (
            cleaned_df
            .dropna()
            .reset_index(drop=True)
        )

    # ========================================================
    # MEAN
    # ========================================================

    elif method == "Mean":

        numeric_columns = (
            cleaned_df
            .select_dtypes(include=np.number)
            .columns
        )

        for column in numeric_columns:

            mean_value = (
                cleaned_df[column].mean()
            )

            if pd.notna(mean_value):

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna(mean_value)
                )

        return cleaned_df

    # ========================================================
    # MEDIAN
    # ========================================================

    elif method == "Median":

        numeric_columns = (
            cleaned_df
            .select_dtypes(include=np.number)
            .columns
        )

        for column in numeric_columns:

            median_value = (
                cleaned_df[column].median()
            )

            if pd.notna(median_value):

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna(median_value)
                )

        return cleaned_df

    # ========================================================
    # MODE
    # ========================================================

    elif method == "Mode":

        for column in cleaned_df.columns:

            mode_values = (
                cleaned_df[column]
                .mode(dropna=True)
            )

            if not mode_values.empty:

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna(mode_values.iloc[0])
                )

            else:

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna("Unknown")
                )

        return cleaned_df

    # ========================================================
    # INVALID METHOD
    # ========================================================

    else:

        raise ValueError(
            f"Unknown missing-value method: {method}"
        )


# ============================================================
# CONVERT DATE COLUMN
# ============================================================

def convert_date_column(
    df,
    column
):
    """
    Convert a column to datetime.
    Invalid values become NaT.
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    if column not in cleaned_df.columns:
        return cleaned_df

    cleaned_df[column] = pd.to_datetime(
        cleaned_df[column],
        errors="coerce"
    )

    return cleaned_df


# ============================================================
# CAP OUTLIERS USING IQR
# ============================================================

def cap_outliers_iqr(
    df,
    column
):
    """
    Cap numerical outliers using
    the Interquartile Range (IQR) method.

    Values below the lower bound are replaced
    by the lower bound.

    Values above the upper bound are replaced
    by the upper bound.
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    if column not in cleaned_df.columns:
        return cleaned_df

    # Make sure the column is numerical
    if not pd.api.types.is_numeric_dtype(
        cleaned_df[column]
    ):

        numeric_series = pd.to_numeric(
            cleaned_df[column],
            errors="coerce"
        )

    else:

        numeric_series = cleaned_df[column]

    valid_series = numeric_series.dropna()

    if valid_series.empty:
        return cleaned_df

    if len(valid_series) < 4:
        return cleaned_df

    # ========================================================
    # IQR CALCULATION
    # ========================================================

    q1 = valid_series.quantile(0.25)
    q3 = valid_series.quantile(0.75)

    iqr = q3 - q1

    if iqr == 0:
        return cleaned_df

    lower_bound = (
        q1 - 1.5 * iqr
    )

    upper_bound = (
        q3 + 1.5 * iqr
    )

    # ========================================================
    # CAP VALUES
    # ========================================================

    cleaned_df[column] = (
        numeric_series
        .clip(
            lower=lower_bound,
            upper=upper_bound
        )
    )

    return cleaned_df


# ============================================================
# REMOVE OUTLIERS USING IQR
# ============================================================

def remove_outliers_iqr(
    df,
    column
):
    """
    Remove rows containing IQR outliers
    from the selected numerical column.
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    if column not in cleaned_df.columns:
        return cleaned_df

    series = pd.to_numeric(
        cleaned_df[column],
        errors="coerce"
    )

    valid_series = series.dropna()

    if len(valid_series) < 4:
        return cleaned_df

    q1 = valid_series.quantile(0.25)
    q3 = valid_series.quantile(0.75)

    iqr = q3 - q1

    if iqr == 0:
        return cleaned_df

    lower_bound = (
        q1 - 1.5 * iqr
    )

    upper_bound = (
        q3 + 1.5 * iqr
    )

    mask = (
        (series >= lower_bound)
        &
        (series <= upper_bound)
    )

    # Keep NaN rows rather than deleting them
    mask = mask | series.isna()

    return (
        cleaned_df.loc[mask]
        .reset_index(drop=True)
    )


# ============================================================
# AUTO CLEAN DATASET
# ============================================================

def auto_clean_dataset(df):
    """
    Automatically perform safe cleaning.

    Steps:
    1. Remove exact duplicate rows.
    2. Fill numerical missing values with median.
    3. Fill categorical missing values with mode.
    """

    df = _safe_dataframe(df)

    cleaned_df = df.copy()

    # ========================================================
    # REMOVE DUPLICATES
    # ========================================================

    cleaned_df = (
        cleaned_df
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # ========================================================
    # NUMERICAL COLUMNS
    # ========================================================

    numeric_columns = (
        cleaned_df
        .select_dtypes(include=np.number)
        .columns
    )

    for column in numeric_columns:

        if cleaned_df[column].isna().any():

            median_value = (
                cleaned_df[column].median()
            )

            if pd.notna(median_value):

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna(median_value)
                )

    # ========================================================
    # CATEGORICAL COLUMNS
    # ========================================================

    categorical_columns = (
        cleaned_df
        .select_dtypes(
            include=[
                "object",
                "category",
                "bool"
            ]
        )
        .columns
    )

    for column in categorical_columns:

        if cleaned_df[column].isna().any():

            mode_values = (
                cleaned_df[column]
                .mode(dropna=True)
            )

            if not mode_values.empty:

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna(mode_values.iloc[0])
                )

            else:

                cleaned_df[column] = (
                    cleaned_df[column]
                    .fillna("Unknown")
                )

    return cleaned_df


# ============================================================
# CLEANING SUMMARY
# ============================================================

def get_cleaning_summary(
    original_df,
    cleaned_df
):
    """
    Compare the original and cleaned datasets.

    Returns:
        dictionary containing cleaning statistics.
    """

    original_df = _safe_dataframe(
        original_df
    )

    cleaned_df = _safe_dataframe(
        cleaned_df
    )

    original_missing = int(
        original_df.isna().sum().sum()
    )

    cleaned_missing = int(
        cleaned_df.isna().sum().sum()
    )

    original_duplicates = int(
        original_df.duplicated().sum()
    )

    cleaned_duplicates = int(
        cleaned_df.duplicated().sum()
    )

    return {
        "original_rows": len(original_df),
        "cleaned_rows": len(cleaned_df),

        "rows_removed": (
            len(original_df)
            - len(cleaned_df)
        ),

        "original_missing": original_missing,

        "remaining_missing": cleaned_missing,

        "missing_values_handled": (
            original_missing
            - cleaned_missing
        ),

        "original_duplicates": (
            original_duplicates
        ),

        "remaining_duplicates": (
            cleaned_duplicates
        ),

        "duplicates_removed": (
            original_duplicates
            - cleaned_duplicates
        ),
    }


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    # Small test dataset
    test_df = pd.DataFrame({
        "Age": [20, 21, 22, 100, np.nan],
        "Salary": [20000, 25000, 30000, 500000, np.nan],
        "City": [
            "Hyderabad",
            "Delhi",
            "Mumbai",
            None,
            "Hyderabad"
        ]
    })

    print("\n==============================")
    print("DataMind AI Data Cleaner Test")
    print("==============================")

    print("\nOriginal Data:")
    print(test_df)

    print("\nData Quality:")
    print(get_data_quality(test_df))

    print("\nQuality Issues:")
    print(scan_data_quality(test_df))

    cleaned = auto_clean_dataset(test_df)

    print("\nCleaned Data:")
    print(cleaned)

    print("\nCleaning Summary:")
    print(
        get_cleaning_summary(
            test_df,
            cleaned
        )
    )