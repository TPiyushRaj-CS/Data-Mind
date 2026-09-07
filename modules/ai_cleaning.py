import os
import json
from dotenv import load_dotenv
from google import genai


load_dotenv()


def get_gemini_client():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(
        api_key=api_key
    )


def generate_cleaning_recommendations(
    issues,
    df
):

    client = get_gemini_client()

    if client is None:

        return {
            "error": (
                "GEMINI_API_KEY was not found "
                "in the .env file."
            )
        }

    if not issues:

        return {
            "recommendations": [],
            "summary": (
                "No major data-quality problems "
                "were detected."
            )
        }

    # --------------------------------------------------------
    # Dataset information
    # --------------------------------------------------------

    column_information = []

    for column in df.columns:

        column_information.append({
            "column": str(column),
            "dtype": str(df[column].dtype),
            "missing": int(
                df[column].isna().sum()
            ),
            "unique_values": int(
                df[column].nunique(
                    dropna=True
                )
            )
        })

    prompt = f"""
You are a professional Data Quality Analyst.

Analyze the following dataset quality problems.

DATASET COLUMNS:
{json.dumps(
    column_information,
    indent=2
)}

DETECTED PROBLEMS:
{json.dumps(
    issues,
    indent=2,
    default=str
)}

For every detected problem:

1. Explain the problem clearly.
2. Explain why it matters.
3. Recommend the safest cleaning method.
4. Explain why that method is appropriate.
5. Give the user a practical recommendation.

IMPORTANT:

- Do NOT invent dataset values.
- Do NOT recommend deleting data unless necessary.
- Do NOT automatically change the dataset.
- Outliers may be legitimate business values.
- Keep recommendations practical for a Data Analyst.

Return the response in this structure:

DATA QUALITY SUMMARY

<short overall assessment>

RECOMMENDATIONS

For each problem:

Column:
Problem:
Severity:
Recommendation:
Reason:
Suggested Action:

FINAL ADVICE

<short professional conclusion>
"""

    try:

        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        return {
            "recommendations": response.text,
            "summary": "AI analysis completed."
        }

    except Exception as e:

        return {
            "error": str(e)
        }


def create_cleaning_plan(issues, df):
    """
    Creates a safe deterministic cleaning plan
    based on detected data-quality issues.
    """

    plan = []

    for issue in issues:

        issue_type = issue["type"]
        column = issue["column"]

        # ----------------------------------------------------
        # Missing numerical values
        # ----------------------------------------------------

        if issue_type == "Missing Values":

            if column in df.select_dtypes(
                include="number"
            ).columns:

                median_value = df[column].median()

                plan.append({
                    "action": "Fill Missing Values",
                    "column": column,
                    "method": "median",
                    "value": median_value,
                    "description": (
                        f"Fill missing values in "
                        f"{column} using median "
                        f"({median_value:.2f})"
                    ),
                    "recommended": True
                })

            # ------------------------------------------------
            # Missing categorical values
            # ------------------------------------------------

            else:

                mode = df[column].mode()

                if not mode.empty:

                    mode_value = mode.iloc[0]

                else:

                    mode_value = "Unknown"

                plan.append({
                    "action": "Fill Missing Values",
                    "column": column,
                    "method": "mode",
                    "value": mode_value,
                    "description": (
                        f"Fill missing values in "
                        f"{column} using mode "
                        f"({mode_value})"
                    ),
                    "recommended": True
                })

        # ----------------------------------------------------
        # Duplicate rows
        # ----------------------------------------------------

        elif issue_type == "Duplicate Rows":

            plan.append({
                "action": "Remove Duplicates",
                "column": "Entire Dataset",
                "method": "drop_duplicates",
                "value": None,
                "description": (
                    f"Remove {issue['count']:,} "
                    f"duplicate rows"
                ),
                "recommended": True
            })

        # ----------------------------------------------------
        # Invalid dates
        # ----------------------------------------------------

        elif issue_type == "Invalid Dates":

            plan.append({
                "action": "Convert Date",
                "column": column,
                "method": "datetime",
                "value": None,
                "description": (
                    f"Convert {column} "
                    f"to datetime format"
                ),
                "recommended": True
            })

        # ----------------------------------------------------
        # Outliers
        # ----------------------------------------------------

        elif issue_type == "Outliers":

            plan.append({
                "action": "Review Outliers",
                "column": column,
                "method": "review",
                "value": None,
                "description": (
                    f"{issue['count']:,} potential "
                    f"outliers detected in {column}. "
                    f"Review before modifying."
                ),
                "recommended": False
            })

    return plan

