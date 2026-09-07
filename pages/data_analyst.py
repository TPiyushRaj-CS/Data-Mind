import streamlit as st
import pandas as pd
from pathlib import Path


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Data Analyst | DataMind AI",
    page_icon="DataMind",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# LOAD PROJECT CSS
# ============================================================

css_path = Path(__file__).resolve().parent.parent / "styles" / "main.css"

if css_path.exists():
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()

        st.html(f"<style>{css}</style>")

    except Exception:
        pass


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from modules.data_cleaner import (
    get_data_quality,
    remove_duplicates,
    handle_missing_values,
    cap_outliers_iqr
)

from modules.visualization import (
    get_numeric_columns,
    get_categorical_columns,
    create_histogram,
    create_box_plot,
    create_bar_chart,
    create_scatter_plot,
    create_correlation_heatmap
)

from modules.ai_insights import (
    generate_ai_insights
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_quality_score(dataframe):
    """
    Calculate a simple data quality score based on
    missing cells and duplicate rows.
    """

    if dataframe.empty:
        return 0.0

    total_cells = max(
        dataframe.shape[0] * dataframe.shape[1],
        1
    )

    missing_cells = int(
        dataframe.isna().sum().sum()
    )

    duplicate_rows = int(
        dataframe.duplicated().sum()
    )

    missing_rate = missing_cells / total_cells

    duplicate_rate = (
        duplicate_rows / max(len(dataframe), 1)
    )

    score = (
        100
        - (missing_rate * 70)
        - (duplicate_rate * 30)
    )

    return max(
        0.0,
        min(100.0, round(score, 1))
    )


def load_uploaded_dataset(uploaded_file):
    """
    Load CSV or Excel dataset safely.
    """

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)

    if file_name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    raise ValueError(
        "Unsupported file format. Please upload CSV, XLSX or XLS."
    )


def display_metric_card(title, value, subtitle=""):
    """
    Premium metric card matching the DataMind AI
    pastel SaaS theme.
    """

    st.html(
        f"""
        <div class="glass-card" style="
            padding:20px;
            min-height:120px;
            margin-bottom:10px;
        ">

            <div style="
                color:#64748b;
                font-size:0.85rem;
                font-weight:650;
                letter-spacing:0.2px;
            ">
                {title}
            </div>

            <div style="
                color:#1e293b;
                font-size:1.55rem;
                font-weight:750;
                margin-top:7px;
            ">
                {value}
            </div>

            <div style="
                color:#94a3b8;
                font-size:0.75rem;
                margin-top:5px;
            ">
                {subtitle}
            </div>

        </div>
        """
    )


# ============================================================
# PAGE HEADER
# ============================================================

st.html(
    """
    <div class="hero">

        <div style="
            color:#6d28d9;
            font-size:0.9rem;
            font-weight:700;
            letter-spacing:1px;
            margin-bottom:10px;
        ">
            DATAMIND AI | INTELLIGENT ANALYTICS
        </div>

        <div class="hero-title">
            AI Data Analyst
        </div>

        <div class="hero-subtitle">
            Transform raw datasets into clean data,
            meaningful visualizations and intelligent insights.
            <br><br>

            <span style="
                color:#6d28d9;
                font-weight:650;
            ">
                Upload
                &rarr;
                Profile
                &rarr;
                Clean
                &rarr;
                Visualize
                &rarr;
                Analyze
            </span>
        </div>

    </div>
    """
)


# ============================================================
# DATA UPLOAD SECTION
# ============================================================

st.html(
    """
    <div style="
        margin-top:10px;
        margin-bottom:12px;
    ">

        <h2>
            Upload Your Dataset
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Supported formats: CSV, XLSX and XLS
        </p>

    </div>
    """
)


uploaded_file = st.file_uploader(
    "Drop your dataset here",
    type=["csv", "xlsx", "xls"],
    help="Upload a CSV or Excel file to start your analysis.",
    label_visibility="collapsed"
)


# ============================================================
# LOAD DATASET
# ============================================================

if uploaded_file is not None:

    file_signature = (
        uploaded_file.name,
        uploaded_file.size
    )

    previous_signature = st.session_state.get(
        "data_analyst_file_signature"
    )

    if previous_signature != file_signature:

        try:

            df = load_uploaded_dataset(
                uploaded_file
            )

            if df.empty:
                st.error(
                    "The uploaded dataset is empty. Please upload a dataset containing data."
                )
                st.stop()

            st.session_state["df"] = df.copy()

            st.session_state[
                "data_analyst_file_name"
            ] = uploaded_file.name

            st.session_state[
                "data_analyst_file_signature"
            ] = file_signature

            st.session_state.pop(
                "cleaned_df",
                None
            )

            st.session_state[
                "cleaning_history"
            ] = []

            st.session_state.pop(
                "ai_insights",
                None
            )

            st.success(
                f"{uploaded_file.name} loaded successfully."
            )

        except Exception as e:

            st.error(
                f"Unable to load the dataset: {e}"
            )

            st.stop()


# ============================================================
# EMPTY STATE
# ============================================================

if "df" not in st.session_state:

    st.write("")
    st.write("")

    st.html(
        """
        <div class="glass-card" style="
            text-align:center;
            padding:55px 30px;
            margin-top:20px;
        ">

            <h2>
                Your Data Analysis Workspace
            </h2>

            <p style="
                color:#64748b;
                max-width:650px;
                margin:auto;
                line-height:1.8;
            ">
                Upload a CSV or Excel dataset above and
                DataMind AI will help you understand,
                clean, visualize and analyze your data.
            </p>

        </div>
        """
    )

    st.write("")
    st.write("")

    empty1, empty2, empty3, empty4 = st.columns(4)

    with empty1:
        st.html(
            """
            <div style="text-align:center;">
                <div style="
                    color:#6d28d9;
                    font-size:1.15rem;
                    font-weight:700;
                ">
                    Profile
                </div>

                <p style="
                    color:#64748b;
                    font-size:.8rem;
                ">
                    Understand your dataset
                </p>
            </div>
            """
        )

    with empty2:
        st.html(
            """
            <div style="text-align:center;">
                <div style="
                    color:#6d28d9;
                    font-size:1.15rem;
                    font-weight:700;
                ">
                    Clean
                </div>

                <p style="
                    color:#64748b;
                    font-size:.8rem;
                ">
                    Fix data quality problems
                </p>
            </div>
            """
        )

    with empty3:
        st.html(
            """
            <div style="text-align:center;">
                <div style="
                    color:#6d28d9;
                    font-size:1.15rem;
                    font-weight:700;
                ">
                    Visualize
                </div>

                <p style="
                    color:#64748b;
                    font-size:.8rem;
                ">
                    Discover patterns visually
                </p>
            </div>
            """
        )

    with empty4:
        st.html(
            """
            <div style="text-align:center;">
                <div style="
                    color:#6d28d9;
                    font-size:1.15rem;
                    font-weight:700;
                ">
                    Analyze
                </div>

                <p style="
                    color:#64748b;
                    font-size:.8rem;
                ">
                    Generate AI insights
                </p>
            </div>
            """
        )

    st.stop()


# ============================================================
# GET DATAFRAME
# ============================================================

df = st.session_state["df"]

file_name = st.session_state.get(
    "data_analyst_file_name",
    "Dataset"
)


# ============================================================
# DATASET STATUS
# ============================================================

quality_score = calculate_quality_score(df)

missing_count = int(
    df.isna().sum().sum()
)

duplicate_count = int(
    df.duplicated().sum()
)

numeric_count = len(
    df.select_dtypes(
        include="number"
    ).columns
)

categorical_count = len(
    df.select_dtypes(
        include=[
            "object",
            "category",
            "bool"
        ]
    ).columns
)


st.html(
    f"""
    <div class="glass-card" style="
        padding:16px 22px;
        margin-top:5px;
        margin-bottom:22px;
    ">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            flex-wrap:wrap;
            gap:10px;
        ">

            <div>

                <div style="
                    color:#1e293b;
                    font-weight:700;
                    font-size:1rem;
                ">
                    {file_name}
                </div>

                <div style="
                    color:#64748b;
                    font-size:.8rem;
                    margin-top:4px;
                ">
                    Dataset loaded successfully
                </div>

            </div>

            <div style="
                color:#0f766e;
                font-size:.85rem;
                font-weight:650;
            ">
                Ready for Analysis
            </div>

        </div>

    </div>
    """
)


# ============================================================
# DATASET OVERVIEW
# ============================================================

st.html(
    """
    <div style="margin-bottom:18px;">

        <h2>
            Dataset Overview
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            A quick snapshot of your dataset.
        </p>

    </div>
    """
)


overview1, overview2, overview3, overview4 = st.columns(4)


with overview1:

    display_metric_card(
        "Total Rows",
        f"{len(df):,}",
        "Records in dataset"
    )


with overview2:

    display_metric_card(
        "Total Columns",
        f"{len(df.columns):,}",
        "Features available"
    )


with overview3:

    display_metric_card(
        "Missing Values",
        f"{missing_count:,}",
        "Empty cells detected"
    )


with overview4:

    display_metric_card(
        "Duplicate Rows",
        f"{duplicate_count:,}",
        "Exact duplicates"
    )


# ============================================================
# DATA PREVIEW
# ============================================================

st.write("")
st.write("")


st.html(
    """
    <div style="margin-bottom:15px;">

        <h2>
            Data Preview
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Inspect the first records of your dataset.
        </p>

    </div>
    """
)


with st.expander(
    "Open Dataset Preview",
    expanded=True
):

    preview_rows = st.slider(
        "Rows to preview",
        min_value=5,
        max_value=min(100, max(5, len(df))),
        value=min(20, max(5, len(df))),
        step=5,
        key="preview_rows"
    )

    st.dataframe(
        df.head(preview_rows),
        use_container_width=True,
        height=380,
        hide_index=True
    )


# ============================================================
# COLUMN INTELLIGENCE
# ============================================================

st.write("")
st.write("")


st.html(
    """
    <div style="margin-bottom:15px;">

        <h2>
            Column Intelligence
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Understand the structure and characteristics
            of every column.
        </p>

    </div>
    """
)


column_info = pd.DataFrame(
    {
        "Column": df.columns,
        "Data Type": [
            str(dtype)
            for dtype in df.dtypes
        ],
        "Missing": [
            int(value)
            for value in df.isnull().sum()
        ],
        "Missing %": [
            round(
                (value / len(df)) * 100,
                2
            )
            if len(df) > 0
            else 0
            for value in df.isnull().sum()
        ],
        "Unique Values": [
            int(value)
            for value in df.nunique(
                dropna=True
            )
        ]
    }
)


st.dataframe(
    column_info,
    use_container_width=True,
    hide_index=True,
    height=min(
        450,
        80 + len(column_info) * 38
    )
)


# ============================================================
# DATA QUALITY
# ============================================================

st.write("")
st.write("")


st.html(
    """
    <div style="margin-bottom:15px;">

        <h2>
            Data Quality
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Measure the health and reliability of your dataset.
        </p>

    </div>
    """
)


try:

    quality = get_data_quality(df)

    q1, q2, q3, q4, q5 = st.columns(5)

    with q1:
        display_metric_card(
            "Rows",
            f"{quality['rows']:,}",
            "Dataset records"
        )

    with q2:
        display_metric_card(
            "Columns",
            f"{quality['columns']:,}",
            "Dataset fields"
        )

    with q3:
        display_metric_card(
            "Missing",
            f"{quality['missing_percentage']:.2f}%",
            "Missing data"
        )

    with q4:
        display_metric_card(
            "Duplicates",
            f"{quality['duplicate_percentage']:.2f}%",
            "Duplicate rate"
        )

    with q5:
        display_metric_card(
            "Quality",
            f"{quality['quality_score']:.1f}%",
            "Overall quality"
        )

except Exception as e:

    st.warning(
        f"Could not calculate detailed quality metrics: {e}"
    )


# ============================================================
# QUALITY PROGRESS
# ============================================================

st.write("")

st.progress(
    int(quality_score),
    text=f"Dataset Health Score: {quality_score}/100"
)


# ============================================================
# MISSING VALUE ANALYSIS
# ============================================================

if missing_count > 0:

    with st.expander(
        "View Missing Value Analysis",
        expanded=False
    ):

        missing_df = pd.DataFrame(
            {
                "Column": df.columns,
                "Missing Values": [
                    int(value)
                    for value in df.isnull().sum()
                ]
            }
        )

        missing_df = missing_df[
            missing_df["Missing Values"] > 0
        ]

        if not missing_df.empty:

            missing_df["Missing %"] = (
                missing_df["Missing Values"]
                / len(df)
                * 100
            ).round(2)

            missing_df = missing_df.sort_values(
                "Missing Values",
                ascending=False
            )

            st.dataframe(
                missing_df,
                use_container_width=True,
                hide_index=True
            )

else:

    st.success(
        "Excellent. No missing values detected."
    )


# ============================================================
# COLUMN TYPE SUMMARY
# ============================================================

st.write("")


type1, type2, type3 = st.columns(3)


with type1:

    st.html(
        f"""
        <div class="glass-card" style="
            text-align:center;
            padding:22px;
        ">

            <h3>
                Numerical
            </h3>

            <div style="
                font-size:1.8rem;
                font-weight:750;
                color:#6d28d9;
            ">
                {numeric_count}
            </div>

            <div style="
                color:#64748b;
                font-size:.8rem;
            ">
                Numeric columns
            </div>

        </div>
        """
    )


with type2:

    st.html(
        f"""
        <div class="glass-card" style="
            text-align:center;
            padding:22px;
        ">

            <h3>
                Categorical
            </h3>

            <div style="
                font-size:1.8rem;
                font-weight:750;
                color:#0f766e;
            ">
                {categorical_count}
            </div>

            <div style="
                color:#64748b;
                font-size:.8rem;
            ">
                Category columns
            </div>

        </div>
        """
    )


with type3:

    memory_kb = (
        df.memory_usage(deep=True).sum() / 1024
    )

    st.html(
        f"""
        <div class="glass-card" style="
            text-align:center;
            padding:22px;
        ">

            <h3>
                Dataset Size
            </h3>

            <div style="
                font-size:1.8rem;
                font-weight:750;
                color:#6d28d9;
            ">
                {memory_kb:.1f}
            </div>

            <div style="
                color:#64748b;
                font-size:.8rem;
            ">
                Approx. KB
            </div>

        </div>
        """
    )


# ============================================================
# DATA CLEANING
# ============================================================

st.write("")
st.write("")
st.write("")


st.html(
    """
    <div style="margin-bottom:18px;">

        <h2>
            AI-Ready Data Cleaning
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Prepare your dataset before visualization and AI analysis.
        </p>

    </div>
    """
)


clean_col1, clean_col2 = st.columns(2, gap="large")


# ============================================================
# MISSING VALUE SETTINGS
# ============================================================

with clean_col1:

    st.html(
        """
        <div style="
            margin-bottom:8px;
            color:#6d28d9;
            font-weight:700;
        ">
            Missing Value Strategy
        </div>
        """
    )

    missing_method = st.selectbox(
        "Choose how missing values should be handled",
        [
            "Do Nothing",
            "Drop Rows",
            "Mean",
            "Median",
            "Mode"
        ],
        key="missing_method"
    )

    if missing_method == "Do Nothing":

        st.caption(
            "No missing-value transformation will be applied."
        )

    elif missing_method == "Drop Rows":

        st.caption(
            "Rows containing missing values will be removed."
        )

    else:

        st.caption(
            f"Missing values will be handled using "
            f"{missing_method.lower()}."
        )


# ============================================================
# DUPLICATES + OUTLIERS
# ============================================================

with clean_col2:

    st.html(
        """
        <div style="
            margin-bottom:8px;
            color:#6d28d9;
            font-weight:700;
        ">
            Cleaning Controls
        </div>
        """
    )

    remove_duplicate_option = st.checkbox(
        "Remove duplicate rows",
        value=True,
        key="remove_duplicates"
    )

    remove_outliers = st.checkbox(
        "Cap numerical outliers using IQR",
        value=False,
        key="cap_outliers"
    )


# ============================================================
# CLEAN DATASET BUTTON
# ============================================================

st.write("")


if st.button(
    "Clean Dataset",
    type="primary",
    use_container_width=True,
    key="clean_dataset"
):

    cleaned_df = df.copy()

    cleaning_history = []


    # --------------------------------------------------------
    # HANDLE MISSING VALUES
    # --------------------------------------------------------

    if missing_method != "Do Nothing":

        try:

            before_missing = int(
                cleaned_df.isna().sum().sum()
            )

            cleaned_df = handle_missing_values(
                cleaned_df,
                missing_method
            )

            after_missing = int(
                cleaned_df.isna().sum().sum()
            )

            cleaning_history.append(
                f"Missing values handled using "
                f"'{missing_method}'. "
                f"Before: {before_missing:,}; "
                f"After: {after_missing:,}."
            )

        except Exception as e:

            st.warning(
                f"Could not handle missing values: {e}"
            )


    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    if remove_duplicate_option:

        try:

            before_rows = len(
                cleaned_df
            )

            cleaned_df = remove_duplicates(
                cleaned_df
            )

            after_rows = len(
                cleaned_df
            )

            removed_rows = (
                before_rows - after_rows
            )

            cleaning_history.append(
                f"Removed {removed_rows:,} duplicate rows."
            )

        except Exception as e:

            st.warning(
                f"Could not remove duplicates: {e}"
            )


    # --------------------------------------------------------
    # CAP OUTLIERS
    # --------------------------------------------------------

    if remove_outliers:

        try:

            cleaned_df = cap_outliers_iqr(
                cleaned_df
            )

            cleaning_history.append(
                "Numerical outliers were capped using the IQR method."
            )

        except Exception as e:

            st.warning(
                f"Could not cap outliers: {e}"
            )


    # --------------------------------------------------------
    # SAVE CLEANED DATA
    # --------------------------------------------------------

    st.session_state[
        "cleaned_df"
    ] = cleaned_df

    st.session_state[
        "cleaning_history"
    ] = cleaning_history

    st.success(
        "Dataset cleaned successfully."
    )

    st.rerun()


# ============================================================
# CLEANED DATASET
# ============================================================

if "cleaned_df" in st.session_state:

    cleaned_df = st.session_state[
        "cleaned_df"
    ]

    cleaning_history = st.session_state.get(
        "cleaning_history",
        []
    )


    st.write("")
    st.write("")


    st.html(
        """
        <div style="margin-bottom:18px;">

            <h2>
                Cleaned Dataset
            </h2>

            <p style="
                color:#64748b;
                margin-top:-8px;
            ">
                Review the results of your cleaning operations.
            </p>

        </div>
        """
    )


    # --------------------------------------------------------
    # BEFORE / AFTER METRICS
    # --------------------------------------------------------

    before_rows = len(df)
    after_rows = len(cleaned_df)

    before_missing = int(
        df.isna().sum().sum()
    )

    after_missing = int(
        cleaned_df.isna().sum().sum()
    )

    before_quality = calculate_quality_score(
        df
    )

    after_quality = calculate_quality_score(
        cleaned_df
    )


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "Original Rows",
            f"{before_rows:,}"
        )


    with c2:

        st.metric(
            "Cleaned Rows",
            f"{after_rows:,}",
            delta=f"{after_rows - before_rows:,}"
        )


    with c3:

        st.metric(
            "Missing Values",
            f"{after_missing:,}",
            delta=f"{after_missing - before_missing:,}"
        )


    with c4:

        st.metric(
            "Quality Score",
            f"{after_quality:.1f}%",
            delta=f"{after_quality - before_quality:+.1f}%"
        )


    # --------------------------------------------------------
    # QUALITY COMPARISON
    # --------------------------------------------------------

    st.write("")


    comparison1, comparison2 = st.columns(2)


    with comparison1:

        st.progress(
            int(before_quality),
            text=f"Before Cleaning: {before_quality}/100"
        )


    with comparison2:

        st.progress(
            int(after_quality),
            text=f"After Cleaning: {after_quality}/100"
        )


    # --------------------------------------------------------
    # CLEANING HISTORY
    # --------------------------------------------------------

    if cleaning_history:

        with st.expander(
            "View Cleaning History",
            expanded=True
        ):

            for index, action in enumerate(
                cleaning_history,
                start=1
            ):

                st.markdown(
                    f"**{index}.** {action}"
                )


    # --------------------------------------------------------
    # CLEANED PREVIEW
    # --------------------------------------------------------

    with st.expander(
        "Preview Cleaned Dataset",
        expanded=True
    ):

        st.dataframe(
            cleaned_df.head(100),
            use_container_width=True,
            height=400,
            hide_index=True
        )


    # --------------------------------------------------------
    # DOWNLOAD CLEANED DATASET
    # --------------------------------------------------------

    csv_data = (
        cleaned_df
        .to_csv(index=False)
        .encode("utf-8")
    )


    st.download_button(
        "Download Cleaned Dataset",
        data=csv_data,
        file_name="cleaned_dataset.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary"
    )


# ============================================================
# STATISTICAL ANALYSIS
# ============================================================

st.write("")
st.write("")
st.write("")


st.html(
    """
    <div style="margin-bottom:18px;">

        <h2>
            Statistical Analysis
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Explore descriptive statistics and numerical patterns.
        </p>

    </div>
    """
)


stats_tab1, stats_tab2 = st.tabs(
    [
        "Full Statistics",
        "Numerical Summary"
    ]
)


with stats_tab1:

    try:

        statistics = df.describe(
            include="all"
        ).T

        st.dataframe(
            statistics,
            use_container_width=True,
            height=450
        )

    except Exception as e:

        st.info(
            f"Statistical summary is not available: {e}"
        )


with stats_tab2:

    if numeric_count > 0:

        try:

            numeric_summary = (
                df
                .select_dtypes(
                    include="number"
                )
                .describe()
                .T
            )

            st.dataframe(
                numeric_summary,
                use_container_width=True,
                height=400
            )

        except Exception as e:

            st.warning(
                f"Could not generate numerical summary: {e}"
            )

    else:

        st.info(
            "No numerical columns were detected."
        )


# ============================================================
# SMART VISUALIZATION
# ============================================================

st.write("")
st.write("")
st.write("")


st.html(
    """
    <div style="margin-bottom:18px;">

        <h2>
            Smart Data Visualization
        </h2>

        <p style="
            color:#64748b;
            margin-top:-8px;
        ">
            Explore your dataset through interactive visualizations.
        </p>

    </div>
    """
)


# ============================================================
# DETECT COLUMN TYPES
# ============================================================

try:

    numeric_columns = get_numeric_columns(
        df
    )

except Exception:

    numeric_columns = (
        df
        .select_dtypes(
            include="number"
        )
        .columns
        .tolist()
    )


try:

    categorical_columns = get_categorical_columns(
        df
    )

except Exception:

    categorical_columns = (
        df
        .select_dtypes(
            include=[
                "object",
                "category",
                "bool"
            ]
        )
        .columns
        .tolist()
    )


# ============================================================
# COLUMN SUMMARY
# ============================================================

visual1, visual2 = st.columns(2)


with visual1:

    st.html(
        f"""
        <div class="glass-card">

            <h3>
                Numerical Columns
            </h3>

            <p style="
                color:#64748b;
                line-height:1.7;
            ">
                {len(numeric_columns)} numerical columns
                available for histograms, box plots,
                scatter plots and correlation analysis.
            </p>

        </div>
        """
    )


with visual2:

    st.html(
        f"""
        <div class="glass-card">

            <h3>
                Categorical Columns
            </h3>

            <p style="
                color:#64748b;
                line-height:1.7;
            ">
                {len(categorical_columns)} categorical columns
                available for category-based visualizations.
            </p>

        </div>
        """
    )


st.write("")


# ============================================================
# VISUALIZATION TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Histogram",
        "Box Plot",
        "Bar Chart",
        "Scatter Plot",
        "Correlation"
    ]
)


# ============================================================
# HISTOGRAM
# ============================================================

with tab1:

    if numeric_columns:

        selected_column = st.selectbox(
            "Select numerical column",
            numeric_columns,
            key="histogram_column"
        )

        try:

            fig = create_histogram(
                df,
                selected_column
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Unable to create histogram: {e}"
            )

    else:

        st.warning(
            "No numerical columns are available."
        )


# ============================================================
# BOX PLOT
# ============================================================

with tab2:

    if numeric_columns:

        selected_column = st.selectbox(
            "Select numerical column",
            numeric_columns,
            key="box_column"
        )

        try:

            fig = create_box_plot(
                df,
                selected_column
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Unable to create box plot: {e}"
            )

    else:

        st.warning(
            "No numerical columns are available."
        )


# ============================================================
# BAR CHART
# ============================================================

with tab3:

    if categorical_columns:

        selected_column = st.selectbox(
            "Select categorical column",
            categorical_columns,
            key="bar_column"
        )

        try:

            fig = create_bar_chart(
                df,
                selected_column
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Unable to create bar chart: {e}"
            )

    else:

        st.warning(
            "No categorical columns are available."
        )


# ============================================================
# SCATTER PLOT
# ============================================================

with tab4:

    if len(numeric_columns) >= 2:

        scatter_col1, scatter_col2 = st.columns(2)


        with scatter_col1:

            x_column = st.selectbox(
                "X-axis",
                numeric_columns,
                key="scatter_x"
            )


        with scatter_col2:

            y_column = st.selectbox(
                "Y-axis",
                numeric_columns,
                key="scatter_y"
            )


        try:

            fig = create_scatter_plot(
                df,
                x_column,
                y_column
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"Unable to create scatter plot: {e}"
            )

    else:

        st.warning(
            "At least two numerical columns are required."
        )


# ============================================================
# CORRELATION HEATMAP
# ============================================================

with tab5:

    if len(numeric_columns) >= 2:

        try:

            fig = create_correlation_heatmap(
                df
            )

            if fig is not None:

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            else:

                st.info(
                    "Correlation heatmap could not be generated."
                )

        except Exception as e:

            st.error(
                f"Unable to create correlation heatmap: {e}"
            )

    else:

        st.warning(
            "At least two numerical columns are required."
        )


# ============================================================
# AI POWERED INSIGHTS
# ============================================================

st.write("")
st.write("")
st.write("")


st.html(
    """
    <div class="hero" style="
        padding:32px;
        margin-top:20px;
    ">

        <div style="
            color:#6d28d9;
            font-size:.85rem;
            font-weight:700;
            letter-spacing:1px;
        ">
            GEMINI INTELLIGENCE
        </div>

        <div style="
            color:#1e293b;
            font-size:2rem;
            font-weight:800;
            margin-top:7px;
        ">
            AI-Powered Data Insights
        </div>

        <div style="
            color:#64748b;
            font-size:1rem;
            line-height:1.7;
            margin-top:8px;
        ">
            Let DataMind AI analyze your dataset and identify
            important patterns, trends, data-quality concerns
            and business recommendations.
        </div>

    </div>
    """
)


# ============================================================
# AI INSIGHT FEATURES
# ============================================================

ai1, ai2, ai3, ai4 = st.columns(4)


with ai1:

    st.html(
        """
        <div style="
            text-align:center;
            padding:15px;
        ">
            <b>Executive Summary</b>
        </div>
        """
    )


with ai2:

    st.html(
        """
        <div style="
            text-align:center;
            padding:15px;
        ">
            <b>Key Findings</b>
        </div>
        """
    )


with ai3:

    st.html(
        """
        <div style="
            text-align:center;
            padding:15px;
        ">
            <b>Trends and Relationships</b>
        </div>
        """
    )


with ai4:

    st.html(
        """
        <div style="
            text-align:center;
            padding:15px;
        ">
            <b>Recommendations</b>
        </div>
        """
    )


# ============================================================
# SELECT DATA FOR AI
# ============================================================

analysis_source = st.radio(
    "Choose data for AI analysis",
    [
        "Original Dataset",
        "Cleaned Dataset"
    ],
    horizontal=True,
    disabled="cleaned_df" not in st.session_state,
    key="ai_analysis_source"
)


if (
    analysis_source == "Cleaned Dataset"
    and "cleaned_df" in st.session_state
):

    analysis_df = st.session_state[
        "cleaned_df"
    ]

else:

    analysis_df = df


st.caption(
    f"AI will analyze {len(analysis_df):,} rows "
    f"and {len(analysis_df.columns):,} columns."
)


# ============================================================
# GENERATE AI INSIGHTS
# ============================================================

if st.button(
    "Generate AI Insights",
    type="primary",
    use_container_width=True,
    key="generate_ai_insights"
):

    with st.spinner(
        "DataMind AI is analyzing your dataset..."
    ):

        try:

            insights = generate_ai_insights(
                analysis_df
            )

            st.session_state[
                "ai_insights"
            ] = insights

            st.success(
                "AI analysis completed successfully."
            )

        except Exception as e:

            st.error(
                f"AI analysis failed: {e}"
            )


# ============================================================
# DISPLAY SAVED AI INSIGHTS
# ============================================================

if "ai_insights" in st.session_state:

    st.write("")


    st.html(
        """
        <div class="glass-card" style="
            border-color:rgba(167,139,250,.45);
            margin-top:15px;
            margin-bottom:20px;
        ">

            <div style="
                color:#6d28d9;
                font-size:.8rem;
                font-weight:700;
                letter-spacing:1px;
            ">
                DATAMIND AI ANALYSIS
            </div>

            <div style="
                color:#1e293b;
                font-size:1.5rem;
                font-weight:750;
                margin-top:5px;
            ">
                Intelligent Dataset Report
            </div>

            <div style="
                color:#64748b;
                font-size:.8rem;
                margin-top:5px;
            ">
                Generated using Gemini
            </div>

        </div>
        """
    )


    st.markdown(
        st.session_state[
            "ai_insights"
        ]
    )


# ============================================================
# FINAL SUMMARY SECTION
# ============================================================

st.write("")
st.write("")
st.write("")


st.html(
    """
    <div style="
        text-align:center;
        margin-top:35px;
        margin-bottom:20px;
    ">

        <h2>
            Analysis Complete
        </h2>

        <p style="
            color:#64748b;
        ">
            Your dataset has been explored with DataMind AI.
        </p>

    </div>
    """
)


# ============================================================
# FINAL SUMMARY CARDS
# ============================================================

f1, f2, f3, f4 = st.columns(4)


with f1:

    st.html(
        f"""
        <div class="glass-card" style="
            text-align:center;
        ">

            <h3>
                {len(df):,}
            </h3>

            <p style="color:#64748b;">
                Rows analyzed
            </p>

        </div>
        """
    )


with f2:

    st.html(
        f"""
        <div class="glass-card" style="
            text-align:center;
        ">

            <h3>
                {len(df.columns):,}
            </h3>

            <p style="color:#64748b;">
                Columns analyzed
            </p>

        </div>
        """
    )


with f3:

    st.html(
        f"""
        <div class="glass-card" style="
            text-align:center;
        ">

            <h3>
                {quality_score:.1f}%
            </h3>

            <p style="color:#64748b;">
                Data quality
            </p>

        </div>
        """
    )


with f4:

    st.html(
        """
        <div class="glass-card" style="
            text-align:center;
        ">

            <h3>
                Gemini
            </h3>

            <p style="color:#64748b;">
                AI engine
            </p>

        </div>
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.write("")
st.write("")
st.write("")


st.html(
    """
    <div class="footer">

        <div style="
            font-size:1.05rem;
            color:#64748b;
        ">
            <strong>DataMind AI</strong>
        </div>

        <div style="margin-top:7px;">
            AI Data Analyst | Data Cleaning | Visualization | Insights
        </div>

        <div style="
            margin-top:7px;
            color:#64748b;
        ">
            Built with Python + Pandas + Streamlit + Gemini
        </div>

        <div style="
            margin-top:12px;
            color:#475569;
            font-size:.75rem;
        ">
            Copyright 2026 DataMind AI
        </div>

    </div>
    """
)