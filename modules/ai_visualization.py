import os
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    """
    Create and return the Gemini client using the API key
    stored in the .env file.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


# ============================================================
# VISUALIZATION RECOMMENDATIONS
# ============================================================

def get_visualization_recommendations(df):
    """
    Analyze the dataset and ask Gemini to recommend
    useful visualizations.

    Returns:
        {
            "recommendations": [...]
        }

    or:

        {
            "error": "..."
        }
    """

    # --------------------------------------------------------
    # Validate dataframe
    # --------------------------------------------------------

    if df is None:
        return {
            "error": "No dataset was provided."
        }

    if not isinstance(df, pd.DataFrame):
        return {
            "error": "The provided data is not a valid DataFrame."
        }

    if df.empty:
        return {
            "error": "The dataset is empty."
        }

    # --------------------------------------------------------
    # Get Gemini client
    # --------------------------------------------------------

    client = get_gemini_client()

    if client is None:
        return {
            "error": (
                "GEMINI_API_KEY was not found "
                "in the .env file."
            )
        }

    # --------------------------------------------------------
    # Collect dataset information
    # --------------------------------------------------------

    column_info = []

    for column in df.columns:

        column_info.append({
            "column": str(column),
            "dtype": str(df[column].dtype),
            "unique_values": int(
                df[column].nunique(dropna=True)
            ),
            "missing_values": int(
                df[column].isna().sum()
            )
        })

    # --------------------------------------------------------
    # Dataset size
    # --------------------------------------------------------

    dataset_info = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_details": column_info
    }

    # --------------------------------------------------------
    # Gemini prompt
    # --------------------------------------------------------

    prompt = f"""
You are an expert Data Analyst working inside an
AI-powered data analytics application called DataMind AI.

Analyze the dataset information below and recommend
the most useful visualizations.

DATASET INFORMATION:

{json.dumps(dataset_info, indent=2)}

Recommend up to 8 useful charts.

Your recommendations should focus on:
- Comparing categories
- Understanding distributions
- Finding trends over time
- Understanding relationships between numerical columns
- Identifying unusual values or outliers
- Showing proportions when appropriate

For each recommended chart provide:

1. Chart title
2. Chart type
3. X-axis column
4. Y-axis column if required
5. Reason why the chart is useful

Only use columns that actually exist in the dataset.

Return ONLY valid JSON.

Use exactly this structure:

[
    {{
        "title": "Employees by Department",
        "chart_type": "bar",
        "x_column": "Department",
        "y_column": null,
        "reason": "Compare employee counts across departments."
    }}
]

Valid chart types:

bar
line
scatter
histogram
pie
box
area

Rules:

- Do not invent column names.
- Do not recommend a chart if the required columns do not exist.
- Use histogram for numerical distributions.
- Use box plots for numerical distributions and outlier detection.
- Use scatter plots for relationships between numerical columns.
- Use line or area charts when a meaningful time/date column exists.
- Use bar charts for category comparisons.
- Use pie charts only when there are a small number of categories.
- Keep recommendations relevant to the dataset.
- Return only JSON.
"""

    # --------------------------------------------------------
    # Generate recommendations
    # --------------------------------------------------------

    try:

        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        if not response or not response.text:
            return {
                "error": "Gemini returned an empty response."
            }

        text = response.text.strip()

        # ----------------------------------------------------
        # Remove markdown JSON code fences
        # ----------------------------------------------------

        if text.startswith("```"):

            text = text.replace(
                "```json",
                "",
                1
            )

            if text.endswith("```"):
                text = text[:-3]

            text = text.strip()

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        recommendations = json.loads(text)

        # ----------------------------------------------------
        # Validate response structure
        # ----------------------------------------------------

        if not isinstance(recommendations, list):
            return {
                "error": (
                    "Gemini returned an invalid "
                    "recommendation format."
                )
            }

        # ----------------------------------------------------
        # Validate recommended columns
        # ----------------------------------------------------

        valid_columns = {
            str(column)
            for column in df.columns
        }

        validated_recommendations = []

        for recommendation in recommendations:

            if not isinstance(
                recommendation,
                dict
            ):
                continue

            x_column = recommendation.get(
                "x_column"
            )

            y_column = recommendation.get(
                "y_column"
            )

            # Validate X column
            if (
                x_column is not None
                and str(x_column) not in valid_columns
            ):
                continue

            # Validate Y column
            if (
                y_column is not None
                and str(y_column) not in valid_columns
            ):
                continue

            validated_recommendations.append(
                recommendation
            )

        return {
            "recommendations":
                validated_recommendations[:8]
        }

    except json.JSONDecodeError:

        return {
            "error": (
                "Gemini returned an invalid JSON response."
            )
        }

    except Exception as e:

        return {
            "error": str(e)
        }