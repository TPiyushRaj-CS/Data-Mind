import os
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path

from modules.data_cleaner import (
    scan_data_quality,
    fill_missing_numeric,
    fill_missing_categorical,
    remove_duplicate_rows,
    convert_date_column,
    cap_outliers_iqr,
    auto_clean_dataset,
)


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

st.set_page_config(
    page_title="DataMind AI Dashboard Builder",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# DATAMIND AI LIGHT PASTEL THEME
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
CSS_PATH = BASE_DIR / "styles" / "main.css"

if CSS_PATH.exists():
    try:
        with open(CSS_PATH, "r", encoding="utf-8") as css_file:
            st.html(f"<style>{css_file.read()}</style>")
    except Exception:
        pass


st.html(
    """
    <style>
        .dashboard-hero {
            padding: 30px 34px;
            border-radius: 24px;
            margin-bottom: 24px;
            background: linear-gradient(135deg, #ede9fe 0%, #e0f2fe 52%, #ecfeff 100%);
            border: 1px solid #ddd6fe;
            box-shadow: 0 18px 45px rgba(99, 102, 241, 0.10);
        }

        .dashboard-hero .section-label {
            color: #6d28d9;
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .dashboard-hero h1 {
            color: #1e293b;
            margin: 0;
            font-size: 2.35rem;
            font-weight: 800;
            letter-spacing: -1px;
        }

        .dashboard-hero p {
            color: #64748b;
            margin: 9px 0 0;
            max-width: 900px;
            font-size: 1rem;
            line-height: 1.7;
        }

        .dashboard-panel {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid #e2e8f0;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
        }

        .dashboard-status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 999px;
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            color: #047857;
            font-size: 12px;
            font-weight: 700;
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.80);
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.05);
        }

        [data-testid="stMetricLabel"] {
            color: #64748b !important;
        }

        [data-testid="stMetricValue"] {
            color: #1e293b !important;
        }

        div[data-testid="stFileUploader"] {
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 8px;
        }

        div[data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #7c3aed, #6366f1);
        }

        .stButton > button {
            border-radius: 12px;
            border: 1px solid #ddd6fe;
            background: #ffffff;
            color: #4c1d95;
        }

        .stButton > button:hover {
            border-color: #a78bfa;
            color: #6d28d9;
            background: #faf5ff;
        }
    </style>
    """
)


def style_plotly_figure(fig):
    """Apply the DataMind AI pastel palette to a Plotly figure."""
    if fig is None:
        return fig

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.78)",
        font=dict(color="#334155", family="Arial, sans-serif"),
        title_font=dict(color="#1e293b", size=18),
        colorway=[
            "#7c3aed",
            "#6366f1",
            "#06b6d4",
            "#a78bfa",
            "#818cf8",
            "#67e8f9",
        ],
        margin=dict(l=20, r=20, t=55, b=20),
    )

    fig.update_xaxes(
        gridcolor="#e2e8f0",
        linecolor="#cbd5e1",
        zerolinecolor="#e2e8f0",
        tickfont=dict(color="#64748b"),
        title_font=dict(color="#475569"),
    )

    fig.update_yaxes(
        gridcolor="#e2e8f0",
        linecolor="#cbd5e1",
        zerolinecolor="#e2e8f0",
        tickfont=dict(color="#64748b"),
        title_font=dict(color="#475569"),
    )

    return fig


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"

BUSINESS_NUMERIC_KEYWORDS = [
    "sales",
    "revenue",
    "profit",
    "amount",
    "price",
    "income",
    "cost",
    "expense",
    "quantity",
    "units",
    "salary",
    "balance",
    "charges",
    "rating",
    "score",
    "value",
    "total",
    "discount",
    "tax",
    "cltv",
]

ID_KEYWORDS = [
    "id",
    "_id",
    "code",
    "zip",
    "pincode",
    "pin_code",
    "phone",
    "mobile",
    "account_number",
    "account_no",
    "transaction_id",
    "customer_id",
    "order_id",
    "product_id",
    "user_id",
]


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(show_spinner=False)
def load_dataset(file_bytes, file_name):
    """Load CSV or Excel data from uploaded bytes."""
    if file_name.lower().endswith(".csv"):
        return pd.read_csv(BytesIO(file_bytes))

    return pd.read_excel(BytesIO(file_bytes))


# ============================================================
# COLUMN DETECTION
# ============================================================

def detect_column_types(df):
    numeric_columns = df.select_dtypes(
        include=np.number
    ).columns.tolist()

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    date_columns = []

    for column in df.columns:
        if column in numeric_columns:
            continue

        try:
            converted = pd.to_datetime(
                df[column],
                errors="coerce"
            )

            valid_ratio = converted.notna().mean()

            if valid_ratio >= 0.80:
                date_columns.append(column)

        except Exception:
            pass

    categorical_columns = [
        column
        for column in categorical_columns
        if column not in date_columns
    ]

    return numeric_columns, categorical_columns, date_columns


def detect_identifier_columns(df):
    identifier_columns = []

    for column in df.columns:
        name = str(column).strip().lower()

        unique_ratio = (
            df[column].nunique(dropna=True)
            / max(len(df), 1)
        )

        keyword_match = any(
            keyword in name
            for keyword in ID_KEYWORDS
        )

        # High-cardinality text is usually not useful
        # as a dashboard category.
        high_cardinality = (
            unique_ratio > 0.95
            and df[column].nunique(dropna=True) > 20
        )

        if keyword_match or high_cardinality:
            identifier_columns.append(column)

    return identifier_columns


def detect_important_numeric_columns(
    df,
    numeric_columns,
    identifier_columns
):
    important = []

    for column in numeric_columns:
        if column in identifier_columns:
            continue

        name = str(column).strip().lower()

        if any(
            keyword in name
            for keyword in BUSINESS_NUMERIC_KEYWORDS
        ):
            important.append(column)

    # If no semantic business measure is found,
    # use numeric columns that are not IDs.
    if not important:
        important = [
            column
            for column in numeric_columns
            if column not in identifier_columns
        ]

    return important


def detect_important_categorical_columns(
    df,
    categorical_columns
):
    important = []

    for column in categorical_columns:
        unique_count = df[column].nunique(dropna=True)

        if 2 <= unique_count <= 30:
            important.append(column)

    return important


# ============================================================
# DATA QUALITY
# ============================================================

def get_missing_values(df):
    missing = df.isnull().sum()

    return missing[
        missing > 0
    ].sort_values(ascending=False)


def get_numeric_summary(df, numeric_columns):
    if not numeric_columns:
        return pd.DataFrame()

    summary = df[numeric_columns].describe().T

    summary["missing"] = (
        df[numeric_columns].isnull().sum()
    )

    summary["missing_%"] = (
        summary["missing"] / max(len(df), 1) * 100
    ).round(2)

    return summary


def detect_kpi_candidates(
    df,
    numeric_columns,
    identifier_columns=None
):
    identifier_columns = identifier_columns or []

    candidates = []

    for column in numeric_columns:
        if column in identifier_columns:
            continue

        if df[column].nunique(dropna=True) > 1:
            candidates.append(column)

    return candidates


# ============================================================
# KPI HELPERS
# ============================================================

def calculate_kpi_value(df, column, aggregation="sum"):
    series = pd.to_numeric(
        df[column],
        errors="coerce"
    ).dropna()

    if series.empty:
        return 0

    if aggregation == "mean":
        return series.mean()

    if aggregation == "count":
        return series.count()

    if aggregation == "max":
        return series.max()

    if aggregation == "min":
        return series.min()

    return series.sum()


def format_kpi(value):
    if value is None or pd.isna(value):
        return "0"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"

    if value.is_integer():
        return f"{int(value):,}"

    return f"{value:,.2f}"


# ============================================================
# CHART GENERATION
# ============================================================

def create_dashboard_charts(
    df,
    numeric_columns,
    categorical_columns,
    date_columns,
    identifier_columns
):
    charts = []

    important_numeric = detect_important_numeric_columns(
        df,
        numeric_columns,
        identifier_columns
    )

    important_categorical = detect_important_categorical_columns(
        df,
        categorical_columns
    )

    # --------------------------------------------------------
    # 1. TIME TREND
    # --------------------------------------------------------
    if date_columns and important_numeric:
        date_col = date_columns[0]
        numeric_col = important_numeric[0]

        temp = df[[date_col, numeric_col]].copy()
        temp[date_col] = pd.to_datetime(
            temp[date_col],
            errors="coerce"
        )
        temp[numeric_col] = pd.to_numeric(
            temp[numeric_col],
            errors="coerce"
        )
        temp = temp.dropna()

        if not temp.empty:
            grouped = (
                temp.groupby(date_col)[numeric_col]
                .sum()
                .reset_index()
                .sort_values(date_col)
            )

            fig = px.line(
                grouped,
                x=date_col,
                y=numeric_col,
                markers=True,
                title=f"{numeric_col} Trend Over Time",
            )

            charts.append({
                "type": "line",
                "title": f"{numeric_col} Trend",
                "figure": fig,
            })

    # --------------------------------------------------------
    # 2. FIRST CATEGORY COMPARISON
    # --------------------------------------------------------
    if important_categorical and important_numeric:
        category_col = important_categorical[0]
        numeric_col = important_numeric[0]

        temp = df[[category_col, numeric_col]].copy()
        temp[numeric_col] = pd.to_numeric(
            temp[numeric_col],
            errors="coerce"
        )
        temp = temp.dropna()

        if not temp.empty:
            grouped = (
                temp.groupby(category_col)[numeric_col]
                .sum()
                .reset_index()
                .sort_values(
                    numeric_col,
                    ascending=False
                )
                .head(10)
            )

            fig = px.bar(
                grouped,
                x=category_col,
                y=numeric_col,
                title=f"{numeric_col} by {category_col}",
                text_auto=".2s",
            )

            charts.append({
                "type": "bar",
                "title": f"{numeric_col} by {category_col}",
                "figure": fig,
            })

    # --------------------------------------------------------
    # 3. SECOND CATEGORY COMPARISON
    # --------------------------------------------------------
    if (
        len(important_categorical) >= 2
        and important_numeric
    ):
        category_col = important_categorical[1]
        numeric_col = important_numeric[0]

        temp = df[[category_col, numeric_col]].copy()
        temp[numeric_col] = pd.to_numeric(
            temp[numeric_col],
            errors="coerce"
        )
        temp = temp.dropna()

        if not temp.empty:
            grouped = (
                temp.groupby(category_col)[numeric_col]
                .sum()
                .reset_index()
                .sort_values(
                    numeric_col,
                    ascending=False
                )
                .head(10)
            )

            fig = px.bar(
                grouped,
                x=category_col,
                y=numeric_col,
                title=f"{numeric_col} by {category_col}",
                text_auto=".2s",
            )

            charts.append({
                "type": "bar",
                "title": f"{numeric_col} by {category_col}",
                "figure": fig,
            })

    # --------------------------------------------------------
    # 4. CATEGORY DISTRIBUTION
    # --------------------------------------------------------
    if important_categorical:
        category_col = important_categorical[0]

        counts = (
            df[category_col]
            .astype(str)
            .value_counts()
            .head(8)
            .reset_index()
        )

        counts.columns = [
            category_col,
            "Count"
        ]

        if not counts.empty:
            fig = px.pie(
                counts,
                names=category_col,
                values="Count",
                title=f"{category_col} Distribution",
            )

            charts.append({
                "type": "pie",
                "title": f"{category_col} Distribution",
                "figure": fig,
            })

    # --------------------------------------------------------
    # 5. NUMERIC DISTRIBUTION
    # --------------------------------------------------------
    if important_numeric:
        numeric_col = important_numeric[0]

        fig = px.histogram(
            df,
            x=numeric_col,
            title=f"{numeric_col} Distribution",
            nbins=30,
        )

        charts.append({
            "type": "histogram",
            "title": f"{numeric_col} Distribution",
            "figure": fig,
        })

    # --------------------------------------------------------
    # 6. NUMERIC RELATIONSHIP
    # --------------------------------------------------------
    if len(important_numeric) >= 2:
        x_col = important_numeric[0]
        y_col = important_numeric[1]

        temp = df[[x_col, y_col]].copy()
        temp[x_col] = pd.to_numeric(
            temp[x_col],
            errors="coerce"
        )
        temp[y_col] = pd.to_numeric(
            temp[y_col],
            errors="coerce"
        )
        temp = temp.dropna()

        if not temp.empty:
            fig = px.scatter(
                temp,
                x=x_col,
                y=y_col,
                title=f"{y_col} vs {x_col}",
            )

            charts.append({
                "type": "scatter",
                "title": f"{y_col} vs {x_col}",
                "figure": fig,
            })

    return charts


# ============================================================
# CUSTOM CHART BUILDER
# ============================================================

def create_custom_chart(
    df,
    chart_type,
    x_column,
    y_column=None,
    aggregation="sum"
):
    if not x_column:
        return None

    temp = df.copy()

    if chart_type in ["Bar", "Line", "Area"]:
        if not y_column:
            return None

        temp[y_column] = pd.to_numeric(
            temp[y_column],
            errors="coerce"
        )

        temp = temp.dropna(
            subset=[x_column, y_column]
        )

        if temp.empty:
            return None

        if aggregation == "mean":
            grouped = (
                temp.groupby(x_column)[y_column]
                .mean()
                .reset_index()
            )
        elif aggregation == "count":
            grouped = (
                temp.groupby(x_column)[y_column]
                .count()
                .reset_index()
            )
        elif aggregation == "max":
            grouped = (
                temp.groupby(x_column)[y_column]
                .max()
                .reset_index()
            )
        elif aggregation == "min":
            grouped = (
                temp.groupby(x_column)[y_column]
                .min()
                .reset_index()
            )
        else:
            grouped = (
                temp.groupby(x_column)[y_column]
                .sum()
                .reset_index()
            )

        grouped = grouped.sort_values(
            y_column,
            ascending=False
        ).head(30)

        if chart_type == "Bar":
            return px.bar(
                grouped,
                x=x_column,
                y=y_column,
                title=f"{aggregation.title()} of {y_column} by {x_column}",
            )

        if chart_type == "Line":
            return px.line(
                grouped,
                x=x_column,
                y=y_column,
                markers=True,
                title=f"{aggregation.title()} of {y_column} by {x_column}",
            )

        return px.area(
            grouped,
            x=x_column,
            y=y_column,
            title=f"{aggregation.title()} of {y_column} by {x_column}",
        )

    if chart_type == "Pie":
        counts = (
            temp[x_column]
            .astype(str)
            .value_counts()
            .head(12)
            .reset_index()
        )

        counts.columns = [
            x_column,
            "Count"
        ]

        return px.pie(
            counts,
            names=x_column,
            values="Count",
            title=f"{x_column} Distribution",
        )

    if chart_type == "Histogram":
        return px.histogram(
            temp,
            x=x_column,
            nbins=30,
            title=f"{x_column} Distribution",
        )

    if chart_type == "Scatter":
        if not y_column:
            return None

        temp[y_column] = pd.to_numeric(
            temp[y_column],
            errors="coerce"
        )
        temp[x_column] = pd.to_numeric(
            temp[x_column],
            errors="coerce"
        )
        temp = temp.dropna(
            subset=[x_column, y_column]
        )

        if temp.empty:
            return None

        return px.scatter(
            temp,
            x=x_column,
            y=y_column,
            title=f"{y_column} vs {x_column}",
        )

    return None


# ============================================================
# AI INSIGHTS
# ============================================================

def generate_dashboard_insights(
    df,
    important_numeric,
    important_categorical,
    date_columns=None
):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return (
            " GEMINI_API_KEY was not found. "
            "Add it to your .env file."
        )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        numeric_summary = []

        for column in important_numeric[:8]:
            series = pd.to_numeric(
                df[column],
                errors="coerce"
            ).dropna()

            if series.empty:
                continue

            numeric_summary.append(
                f"""
{column}:
- Total: {series.sum():,.2f}
- Average: {series.mean():,.2f}
- Minimum: {series.min():,.2f}
- Maximum: {series.max():,.2f}
"""
            )

        category_summary = []

        for column in important_categorical[:5]:
            counts = (
                df[column]
                .astype(str)
                .value_counts()
                .head(5)
            )

            category_summary.append(
                f"{column}:\n{counts.to_string()}"
            )

        date_summary = ""

        if date_columns:
            date_col = date_columns[0]

            dates = pd.to_datetime(
                df[date_col],
                errors="coerce"
            ).dropna()

            if not dates.empty:
                date_summary = (
                    f"Date column: {date_col}\n"
                    f"Start: {dates.min().date()}\n"
                    f"End: {dates.max().date()}\n"
                )

        prompt = f"""
You are a professional Data Analyst reviewing a dashboard.

Analyze ONLY the information provided below.
Do not invent facts or numbers.

Dataset rows: {len(df):,}
Dataset columns: {len(df.columns):,}

NUMERICAL METRICS:
{chr(10).join(numeric_summary)}

CATEGORICAL BREAKDOWN:
{chr(10).join(category_summary)}

{date_summary}

Provide a concise professional analysis with:

###  Key Insights
Give 3 important findings.

###  Trends / Patterns
Mention important patterns supported by the data.

###  Potential Concerns
Mention up to 2 data/business concerns if supported.

###  Recommendations
Give 2 practical recommendations based only on the data.

Use Markdown.
"""

        model_name = os.getenv(
            "GEMINI_MODEL",
            DEFAULT_GEMINI_MODEL
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        return response.text or "No AI response was returned."

    except Exception as exc:
        return (
            " AI insight generation failed.\n\n"
            f"Error: `{exc}`\n\n"
            "If this is a model availability error, set "
            "`GEMINI_MODEL` in your `.env` file to a model "
            "available to your Gemini API key."
        )


# ============================================================
# EXCEL EXPORT
# ============================================================

def create_excel_report(
    original_df,
    filtered_df,
    important_numeric,
    important_categorical
):
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        filtered_df.to_excel(
            writer,
            sheet_name="Filtered Data",
            index=False
        )

        summary_df = pd.DataFrame({
            "Metric": [
                "Original Rows",
                "Columns",
                "Filtered Rows",
                "Missing Values",
                "Duplicate Rows",
            ],
            "Value": [
                len(original_df),
                len(original_df.columns),
                len(filtered_df),
                int(
                    filtered_df.isnull()
                    .sum()
                    .sum()
                ),
                int(filtered_df.duplicated().sum()),
            ],
        })

        summary_df.to_excel(
            writer,
            sheet_name="Dashboard Summary",
            index=False
        )

        if important_numeric:
            numeric_summary = (
                filtered_df[important_numeric]
                .describe()
                .T
                .reset_index()
            )

            numeric_summary.rename(
                columns={"index": "Column"},
                inplace=True
            )

            numeric_summary.to_excel(
                writer,
                sheet_name="Numerical Analysis",
                index=False
            )

        for column in important_categorical[:8]:
            category_summary = (
                filtered_df[column]
                .astype(str)
                .value_counts()
                .reset_index()
            )

            category_summary.columns = [
                column,
                "Count"
            ]

            safe_name = (
                str(column)
                .replace("/", "_")
                .replace("\\", "_")
                .replace("*", "_")
                .replace("?", "_")
                .replace("[", "_")
                .replace("]", "_")
                .replace(":", "_")
            )

            sheet_name = (
                safe_name[:24] + "_Summary"
            )

            category_summary.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False
            )

    output.seek(0)
    return output.getvalue()


# ============================================================
# SESSION STATE
# ============================================================

if "dashboard_df" not in st.session_state:
    st.session_state["dashboard_df"] = None

if "dashboard_file_name" not in st.session_state:
    st.session_state["dashboard_file_name"] = None

if "dashboard_ai_insights" not in st.session_state:
    st.session_state["dashboard_ai_insights"] = None

if "cleaning_issues" not in st.session_state:
    st.session_state["cleaning_issues"] = []

if "cleaning_history" not in st.session_state:
    st.session_state["cleaning_history"] = []

if "cleaning_file_signature" not in st.session_state:
    st.session_state["cleaning_file_signature"] = None


# ============================================================
# HEADER
# ============================================================

st.html(
    """
    <div class="dashboard-hero">
        <div class="section-label">DATAMIND AI / INTELLIGENT ANALYTICS</div>
        <h1>AI Dashboard Builder</h1>
        <p>
            Upload a CSV or Excel dataset and let DataMind AI profile the data,
            build visualizations, apply interactive filters, generate AI insights,
            and export an analysis report.
        </p>
    </div>
    """
)


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    " Upload your dataset",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file.",
)


# ============================================================
# MAIN APPLICATION
# ============================================================

if uploaded_file is not None:

    try:
        file_bytes = uploaded_file.getvalue()

        with st.spinner(" Loading dataset..."):
            df = load_dataset(
                file_bytes,
                uploaded_file.name
            )

        if df.empty:
            st.error(" The uploaded dataset is empty.")
            st.stop()

        # Remove completely empty columns.
        df = df.dropna(
            axis=1,
            how="all"
        )

        # Store the original dataset only when a new file is uploaded.
        file_signature = (uploaded_file.name, len(file_bytes))
        if st.session_state.get("cleaning_file_signature") != file_signature:
            st.session_state["dashboard_df"] = df.copy()
            st.session_state["dashboard_file_name"] = uploaded_file.name
            st.session_state["cleaning_file_signature"] = file_signature
            st.session_state["cleaning_issues"] = []
            st.session_state["cleaning_history"] = []
            st.session_state["dashboard_ai_insights"] = None
        else:
            df = st.session_state.get("dashboard_df", df).copy()

        # Detect columns.
        (
            numeric_columns,
            categorical_columns,
            date_columns,
        ) = detect_column_types(df)

        identifier_columns = detect_identifier_columns(df)

        important_numeric = (
            detect_important_numeric_columns(
                df,
                numeric_columns,
                identifier_columns
            )
        )

        important_categorical = (
            detect_important_categorical_columns(
                df,
                categorical_columns
            )
        )

        st.session_state[
            "dashboard_numeric_columns"
        ] = numeric_columns

        st.session_state[
            "dashboard_categorical_columns"
        ] = categorical_columns

        st.session_state[
            "dashboard_date_columns"
        ] = date_columns

        st.success(
            f" {uploaded_file.name} loaded successfully!"
        )

        # ====================================================
        # DATASET OVERVIEW
        # ====================================================

        st.header(" Dataset Overview")

        total_rows = len(df)
        total_columns = len(df.columns)
        total_missing = int(
            df.isnull().sum().sum()
        )
        duplicate_rows = int(
            df.duplicated().sum()
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                " Rows",
                f"{total_rows:,}"
            )

        with col2:
            st.metric(
                " Columns",
                f"{total_columns:,}"
            )

        with col3:
            st.metric(
                " Missing Values",
                f"{total_missing:,}"
            )

        with col4:
            st.metric(
                " Duplicate Rows",
                f"{duplicate_rows:,}"
            )

        st.divider()

        # ====================================================
        # COLUMN CLASSIFICATION
        # ====================================================

        st.header(" Automatic Column Detection")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.subheader(" Numerical")

            if numeric_columns:
                for column in numeric_columns:
                    st.write(f"• {column}")
            else:
                st.info("No numerical columns detected.")

        with col2:
            st.subheader(" Categorical")

            if categorical_columns:
                for column in categorical_columns:
                    st.write(f"• {column}")
            else:
                st.info("No categorical columns detected.")

        with col3:
            st.subheader(" Date / Time")

            if date_columns:
                for column in date_columns:
                    st.write(f"• {column}")
            else:
                st.info("No date columns detected.")

        with st.expander(" How DataMind AI classified the columns"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(" **Identifier Columns**")
                if identifier_columns:
                    for column in identifier_columns:
                        st.write(f"• {column}")
                else:
                    st.write("None detected.")

            with col2:
                st.write(" **Important Measures**")
                if important_numeric:
                    for column in important_numeric:
                        st.write(f"• {column}")
                else:
                    st.write("None detected.")

            with col3:
                st.write(" **Useful Categories**")
                if important_categorical:
                    for column in important_categorical:
                        st.write(f"• {column}")
                else:
                    st.write("None detected.")

        st.divider()

        # ====================================================
        # DATA QUALITY
        # ====================================================

        st.header(" Data Quality")

        missing_values = get_missing_values(df)

        if missing_values.empty:
            st.success(" No missing values detected.")
        else:
            missing_df = (
                missing_values
                .reset_index()
            )

            missing_df.columns = [
                "Column",
                "Missing Values"
            ]

            missing_df["Missing %"] = (
                missing_df["Missing Values"]
                / len(df)
                * 100
            ).round(2)

            st.dataframe(
                missing_df,
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        # ====================================================
        # AI DATA CLEANING ASSISTANT
        # ====================================================

        st.header(" AI Data Cleaning Assistant")
        st.caption(
            "Scan the dataset, review recommendations, apply safe cleaning actions, "
            "and compare the data quality before and after cleaning."
        )

        scan_col, score_col = st.columns([1, 2])

        with scan_col:
            if st.button(
                " Scan Dataset",
                type="primary",
                use_container_width=True,
                key="scan_cleaning",
            ):
                st.session_state["cleaning_issues"] = scan_data_quality(df)

        # Current quality score
        total_cells = max(df.shape[0] * df.shape[1], 1)
        missing_cells = int(df.isna().sum().sum())
        duplicate_rows_now = int(df.duplicated().sum())
        missing_rate = missing_cells / total_cells
        duplicate_rate = duplicate_rows_now / max(len(df), 1)
        quality_score = max(0, min(100, round(100 - missing_rate * 70 - duplicate_rate * 30, 1)))

        with score_col:
            st.progress(int(quality_score), text=f"Data Quality Score: {quality_score}/100")

        issues = st.session_state.get("cleaning_issues", [])

        if issues:
            issues_df = pd.DataFrame(issues)
            st.subheader(" Detected Problems")
            st.dataframe(issues_df, use_container_width=True, hide_index=True)

            missing_issues = [x for x in issues if x["type"] == "Missing Values"]
            duplicate_issues = [x for x in issues if x["type"] == "Duplicate Rows"]
            outlier_issues = [x for x in issues if x["type"] == "Outliers"]
            date_issues = [x for x in issues if x["type"] == "Invalid Dates"]

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric(" Missing-value columns", len(missing_issues))
            with m2:
                st.metric(" Duplicate rows", sum(x["count"] for x in duplicate_issues))
            with m3:
                st.metric(" Outlier values", sum(x["count"] for x in outlier_issues))
            with m4:
                st.metric(" Invalid dates", sum(x["count"] for x in date_issues))

            st.subheader(" Recommended Actions")

            # Missing values
            for issue in missing_issues:
                column = issue["column"]
                with st.container(border=True):
                    st.markdown(f"** {column}** — {issue['count']:,} missing ({issue['percentage']}%)")
                    if column in df.select_dtypes(include=np.number).columns:
                        median = pd.to_numeric(df[column], errors="coerce").median()
                        st.info(f"Recommended: fill numerical values with median **{median:,.2f}**.")
                        if st.button(f" Fill {column} with Median", key=f"clean_median_{column}"):
                            st.session_state["dashboard_df"] = fill_missing_numeric(df, column, "median")
                            st.session_state["cleaning_history"].append(f"Filled missing values in '{column}' with median.")
                            st.session_state["cleaning_issues"] = scan_data_quality(st.session_state["dashboard_df"])
                            st.rerun()
                    else:
                        mode = df[column].mode(dropna=True)
                        mode_value = mode.iloc[0] if not mode.empty else "Unknown"
                        st.info(f"Recommended: fill categorical values with mode **{mode_value}**.")
                        if st.button(f" Fill {column} with Mode", key=f"clean_mode_{column}"):
                            st.session_state["dashboard_df"] = fill_missing_categorical(df, column)
                            st.session_state["cleaning_history"].append(f"Filled missing values in '{column}' with mode.")
                            st.session_state["cleaning_issues"] = scan_data_quality(st.session_state["dashboard_df"])
                            st.rerun()

            # Duplicates
            if duplicate_issues:
                count = duplicate_issues[0]["count"]
                with st.container(border=True):
                    st.markdown(f"** Duplicate Rows** — {count:,} duplicate rows detected.")
                    st.info("Recommended: remove exact duplicate rows. No business values are changed.")
                    if st.button(" Remove Duplicate Rows", key="remove_duplicate_rows"):
                        before = len(df)
                        st.session_state["dashboard_df"] = remove_duplicate_rows(df)
                        removed = before - len(st.session_state["dashboard_df"])
                        st.session_state["cleaning_history"].append(f"Removed {removed:,} duplicate rows.")
                        st.session_state["cleaning_issues"] = scan_data_quality(st.session_state["dashboard_df"])
                        st.rerun()

            # Invalid dates
            for issue in date_issues:
                column = issue["column"]
                with st.container(border=True):
                    st.markdown(f"** {column}** — {issue['count']:,} invalid date values.")
                    st.info("Recommended: convert valid date strings to datetime; invalid values become blank (NaT).")
                    if st.button(f" Convert {column} to Date", key=f"convert_date_{column}"):
                        st.session_state["dashboard_df"] = convert_date_column(df, column)
                        st.session_state["cleaning_history"].append(f"Converted '{column}' to datetime.")
                        st.session_state["cleaning_issues"] = scan_data_quality(st.session_state["dashboard_df"])
                        st.rerun()

            # Outliers
            for issue in outlier_issues:
                column = issue["column"]
                with st.container(border=True):
                    st.markdown(f"** {column}** — {issue['count']:,} potential outliers detected.")
                    st.warning("Outliers are not automatically deleted. Capping is offered as an optional transformation.")
                    if st.button(f" Cap {column} using IQR", key=f"cap_outlier_{column}"):
                        st.session_state["dashboard_df"] = cap_outliers_iqr(df, column)
                        st.session_state["cleaning_history"].append(f"Capped outliers in '{column}' using IQR bounds.")
                        st.session_state["cleaning_issues"] = scan_data_quality(st.session_state["dashboard_df"])
                        st.rerun()

            st.divider()
            st.subheader(" Automatic Cleaning")
            st.write("Safely removes exact duplicates and fills numeric missing values with median and categorical missing values with mode.")
            if st.button(" Clean Dataset Automatically", key="auto_clean", use_container_width=True):
                before_rows = len(df)
                cleaned = auto_clean_dataset(df)
                st.session_state["dashboard_df"] = cleaned
                st.session_state["cleaning_history"].append(
                    f"Automatic cleaning completed: {before_rows - len(cleaned):,} duplicate rows removed and missing values imputed where possible."
                )
                st.session_state["cleaning_issues"] = scan_data_quality(cleaned)
                st.rerun()

            if st.session_state.get("cleaning_history"):
                with st.expander(" Cleaning History", expanded=False):
                    for item in reversed(st.session_state["cleaning_history"]):
                        st.write(f"• {item}")

        elif st.session_state.get("cleaning_issues") == []:
            st.info("Click ** Scan Dataset** to check for cleaning opportunities.")

        st.divider()

        # ====================================================
        # NUMERICAL STATISTICS
        # ====================================================

        st.header(" Numerical Statistics")

        numeric_summary = get_numeric_summary(
            df,
            numeric_columns
        )

        if numeric_summary.empty:
            st.info(
                "No numerical columns available."
            )
        else:
            st.dataframe(
                numeric_summary,
                use_container_width=True
            )

        st.divider()

        # ====================================================
        # DATA PREVIEW
        # ====================================================

        with st.expander(" Dataset Preview", expanded=False):
            st.dataframe(
                df.head(20),
                use_container_width=True,
                hide_index=True
            )

        st.divider()

        # ====================================================
        # INTERACTIVE FILTERS
        # ====================================================

        st.header(" Dashboard Filters")

        st.caption(
            "Choose filters to update the KPI cards, charts, "
            "and AI analysis."
        )

        filtered_df = df.copy()

        filter_columns = [
            column
            for column in important_categorical
            if df[column].nunique(dropna=True) <= 30
        ]

        if filter_columns:
            filter_cols = st.columns(
                min(len(filter_columns), 3)
            )

            for index, column in enumerate(
                filter_columns
            ):
                with filter_cols[
                    index % len(filter_cols)
                ]:
                    options = sorted(
                        df[column]
                        .dropna()
                        .astype(str)
                        .unique()
                        .tolist()
                    )

                    selected_values = st.multiselect(
                        f" {column}",
                        options=options,
                        default=[],
                        key=f"dashboard_filter_{column}",
                    )

                    if selected_values:
                        filtered_df = filtered_df[
                            filtered_df[column]
                            .astype(str)
                            .isin(selected_values)
                        ]

        if date_columns:
            date_column = date_columns[0]

            date_data = pd.to_datetime(
                df[date_column],
                errors="coerce"
            ).dropna()

            if not date_data.empty:
                min_date = date_data.min().date()
                max_date = date_data.max().date()

                selected_dates = st.date_input(
                    f" {date_column}",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    key="dashboard_date_filter",
                )

                if (
                    isinstance(selected_dates, tuple)
                    and len(selected_dates) == 2
                ):
                    start_date = pd.Timestamp(
                        selected_dates[0]
                    )

                    end_date = (
                        pd.Timestamp(selected_dates[1])
                        + pd.Timedelta(days=1)
                        - pd.Timedelta(seconds=1)
                    )

                    converted_dates = pd.to_datetime(
                        filtered_df[date_column],
                        errors="coerce"
                    )

                    filtered_df = filtered_df[
                        converted_dates.between(
                            start_date,
                            end_date
                        )
                    ]

        st.info(
            f" Showing **{len(filtered_df):,}** "
            f"of **{len(df):,}** rows."
        )

        if filtered_df.empty:
            st.warning(
                " Your filters returned no rows. "
                "Please change the filters."
            )
            st.stop()

        st.divider()

        # ====================================================
        # AUTOMATIC DASHBOARD
        # ====================================================

        st.header(" AI Generated Dashboard")

        st.write(
            "DataMind AI automatically selected KPIs "
            "and visualizations from the filtered dataset."
        )

        # ----------------------------------------------------
        # KPI CARDS
        # ----------------------------------------------------

        st.subheader(" Key Performance Indicators")

        kpi_candidates = detect_kpi_candidates(
            filtered_df,
            numeric_columns,
            identifier_columns
        )

        selected_kpis = kpi_candidates[:4]

        if selected_kpis:
            kpi_columns = st.columns(
                len(selected_kpis)
            )

            for index, column in enumerate(
                selected_kpis
            ):
                with kpi_columns[index]:
                    value = calculate_kpi_value(
                        filtered_df,
                        column,
                        aggregation="sum"
                    )

                    st.metric(
                        label=column,
                        value=format_kpi(value)
                    )
        else:
            st.info(
                "No suitable numerical columns are "
                "available for KPI generation."
            )

        st.divider()

        # ----------------------------------------------------
        # CHARTS
        # ----------------------------------------------------

        st.subheader(
            " Automatically Generated Visualizations"
        )

        charts = create_dashboard_charts(
            filtered_df,
            numeric_columns,
            categorical_columns,
            date_columns,
            identifier_columns,
        )

        if not charts:
            st.warning(
                "Not enough suitable columns were "
                "found to generate charts."
            )
        else:
            for i in range(0, len(charts), 2):
                chart_columns = st.columns(2)

                for j in range(2):
                    chart_index = i + j

                    if chart_index < len(charts):
                        chart = charts[chart_index]

                        with chart_columns[j]:
                            st.plotly_chart(
                                style_plotly_figure(chart["figure"]),
                                use_container_width=True
                            )

        st.divider()

        # ====================================================
        # CUSTOM CHART BUILDER
        # ====================================================

        st.header(" Custom Chart Builder")

        st.caption(
            "Create an additional visualization by choosing "
            "the columns and chart type yourself."
        )

        chart_types = [
            "Bar",
            "Line",
            "Area",
            "Pie",
            "Histogram",
            "Scatter",
        ]

        custom_col1, custom_col2, custom_col3 = st.columns(3)

        with custom_col1:
            custom_chart_type = st.selectbox(
                " Chart Type",
                chart_types,
                key="custom_chart_type",
            )

        with custom_col2:
            custom_x = st.selectbox(
                "X-axis / Category",
                df.columns.tolist(),
                key="custom_x_column",
            )

        with custom_col3:
            y_options = ["None"] + numeric_columns

            custom_y = st.selectbox(
                "Y-axis / Measure",
                y_options,
                key="custom_y_column",
            )

        custom_y_column = (
            None
            if custom_y == "None"
            else custom_y
        )

        aggregation = "sum"

        if custom_chart_type in [
            "Bar",
            "Line",
            "Area"
        ]:
            aggregation = st.selectbox(
                "Aggregation",
                [
                    "sum",
                    "mean",
                    "count",
                    "max",
                    "min",
                ],
                key="custom_aggregation",
            )

        if st.button(
            " Generate Custom Chart",
            type="secondary",
            use_container_width=True,
        ):
            custom_fig = create_custom_chart(
                filtered_df,
                custom_chart_type,
                custom_x,
                custom_y_column,
                aggregation,
            )

            if custom_fig is None:
                st.warning(
                    " The selected columns are not "
                    "compatible with this chart type."
                )
            else:
                st.plotly_chart(
                    style_plotly_figure(custom_fig),
                    use_container_width=True
                )

        st.divider()

        # ====================================================
        # AI INSIGHTS
        # ====================================================

        st.header(" DataMind AI Insights")

        if st.button(
            " Generate Dashboard Insights",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner(
                " Analyzing your filtered dataset..."
            ):
                insights = generate_dashboard_insights(
                    filtered_df,
                    important_numeric,
                    important_categorical,
                    date_columns,
                )

            st.session_state[
                "dashboard_ai_insights"
            ] = insights

        if st.session_state[
            "dashboard_ai_insights"
        ]:
            st.markdown(
                st.session_state[
                    "dashboard_ai_insights"
                ]
            )

        st.divider()

        # ====================================================
        # EXPORT REPORT
        # ====================================================

        st.header(" Download Analysis Report")

        st.write(
            "Download the filtered data and statistical "
            "analysis as an Excel workbook."
        )

        try:
            excel_report = create_excel_report(
                df,
                filtered_df,
                important_numeric,
                important_categorical,
            )

            st.download_button(
                label=" Download Excel Report",
                data=excel_report,
                file_name=(
                    "DataMind_AI_Analysis_Report.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        except Exception as exc:
            st.error(
                f" Could not create Excel report: {exc}"
            )

        st.divider()

        # ====================================================
        # DASHBOARD STATUS
        # ====================================================

        st.success(
            f"""
 **Dashboard generated successfully!**

• {len(selected_kpis)} KPI cards
• {len(charts)} automatic visualizations
• {len(filter_columns)} interactive category filters
• {len(date_columns)} date column(s) detected
• {len(filtered_df):,} rows currently displayed
"""
        )

    except Exception as exc:
        st.error(
            f" Error while processing the dataset: {exc}"
        )

else:

    # ========================================================
    # EMPTY STATE
    # ========================================================

    st.info(
        " Upload a CSV or Excel file above to begin."
    )

    st.markdown(
        """
###  What DataMind AI can do

**1 Understand your dataset**  
Automatically detect numerical, categorical, ID, and date columns.

**2 Analyze data quality**  
Detect missing values and duplicate records.

**3 Generate KPI cards**  
Identify useful numerical measures automatically.

**4 Build a dashboard**  
Generate appropriate charts based on the dataset.

**5 Interactive filtering**  
Filter categories and date ranges.

**6 Custom charts**  
Choose your own chart type and columns.

**7 Generate AI insights**  
Use Gemini to explain patterns and findings.

**8 Export your analysis**  
Download the filtered data and analysis as Excel.
"""
    )
