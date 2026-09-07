import io
from datetime import datetime

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)


def create_ai_report(
    df,
    ai_insights="",
    cleaning_history=None,
    chart_png=None,
):
    """
    Generate a professional PDF report
    from the current DataMind AI dataset.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataset to analyze.

    ai_insights : str
        AI-generated insights.

    cleaning_history : list
        List of cleaning actions performed.

    chart_png : bytes
        PNG image bytes of a generated visualization.

    Returns
    -------
    bytes
        Generated PDF as bytes.
    """

    # --------------------------------------------------------
    # DEFAULT VALUES
    # --------------------------------------------------------

    if cleaning_history is None:
        cleaning_history = []

    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError(
            "A valid pandas DataFrame is required."
        )

    # --------------------------------------------------------
    # CREATE PDF BUFFER
    # --------------------------------------------------------

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Paragraph(
            "DataMind AI — Automated Data Analysis Report",
            title_style,
        )
    )

    story.append(
        Spacer(1, 15)
    )

    story.append(
        Paragraph(
            f"Generated on: "
            f"{datetime.now().strftime('%d %B %Y, %H:%M')}",
            body_style,
        )
    )

    story.append(
        Spacer(1, 20)
    )

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "Executive Summary",
            heading_style,
        )
    )

    summary = (
        f"The dataset contains "
        f"{len(df):,} rows and "
        f"{len(df.columns):,} columns. "
        f"The report summarizes the dataset structure, "
        f"data quality, cleaning actions, numerical "
        f"statistics, generated visualizations, and "
        f"AI-generated analytical insights."
    )

    story.append(
        Paragraph(
            summary,
            body_style,
        )
    )

    story.append(
        Spacer(1, 15)
    )

    # ========================================================
    # DATASET OVERVIEW
    # ========================================================

    story.append(
        Paragraph(
            "Dataset Overview",
            heading_style,
        )
    )

    overview_data = [
        ["Metric", "Value"],
        ["Rows", f"{len(df):,}"],
        ["Columns", f"{len(df.columns):,}"],
        [
            "Missing Values",
            f"{int(df.isna().sum().sum()):,}",
        ],
        [
            "Duplicate Rows",
            f"{int(df.duplicated().sum()):,}",
        ],
    ]

    overview_table = Table(
        overview_data,
        colWidths=[
            3 * inch,
            2 * inch,
        ],
    )

    overview_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
            ]
        )
    )

    story.append(
        overview_table
    )

    story.append(
        Spacer(1, 20)
    )

    # ========================================================
    # COLUMN INFORMATION
    # ========================================================

    story.append(
        Paragraph(
            "Column Information",
            heading_style,
        )
    )

    column_data = [
        [
            "Column",
            "Data Type",
            "Missing",
            "Unique",
        ]
    ]

    for column in df.columns:

        column_data.append(
            [
                str(column),
                str(df[column].dtype),
                str(
                    int(
                        df[column].isna().sum()
                    )
                ),
                str(
                    int(
                        df[column].nunique(
                            dropna=True
                        )
                    )
                ),
            ]
        )

    column_table = Table(
        column_data,
        repeatRows=1,
        colWidths=[
            2.2 * inch,
            1.3 * inch,
            0.9 * inch,
            0.9 * inch,
        ],
    )

    column_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    story.append(
        column_table
    )

    story.append(
        Spacer(1, 20)
    )

    # ========================================================
    # NUMERICAL SUMMARY
    # ========================================================

    numeric_columns = (
        df.select_dtypes(
            include="number"
        ).columns.tolist()
    )

    if numeric_columns:

        story.append(
            Paragraph(
                "Numerical Summary",
                heading_style,
            )
        )

        numeric_data = [
            [
                "Column",
                "Mean",
                "Min",
                "Max",
            ]
        ]

        for column in numeric_columns:

            series = pd.to_numeric(
                df[column],
                errors="coerce",
            ).dropna()

            if series.empty:
                mean_value = "N/A"
                min_value = "N/A"
                max_value = "N/A"
            else:
                mean_value = f"{series.mean():,.2f}"
                min_value = f"{series.min():,.2f}"
                max_value = f"{series.max():,.2f}"

            numeric_data.append(
                [
                    str(column),
                    mean_value,
                    min_value,
                    max_value,
                ]
            )

        numeric_table = Table(
            numeric_data,
            repeatRows=1,
            colWidths=[
                2.8 * inch,
                1.2 * inch,
                1.2 * inch,
                1.2 * inch,
            ],
        )

        numeric_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.grey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.append(
            numeric_table
        )

        story.append(
            Spacer(1, 20)
        )

    # ========================================================
    # DATA CLEANING HISTORY
    # ========================================================

    story.append(
        Paragraph(
            "Data Cleaning History",
            heading_style,
        )
    )

    if cleaning_history:

        for action in cleaning_history:

            safe_action = (
                str(action)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            story.append(
                Paragraph(
                    f"• {safe_action}",
                    body_style,
                )
            )

            story.append(
                Spacer(1, 4)
            )

    else:

        story.append(
            Paragraph(
                "No cleaning actions were recorded.",
                body_style,
            )
        )

    story.append(
        Spacer(1, 20)
    )

    # ========================================================
    # GENERATED VISUALIZATION
    # ========================================================

    if chart_png:

        story.append(
            Paragraph(
                "Generated Visualization",
                heading_style,
            )
        )

        story.append(
            Spacer(1, 10)
        )

        try:

            chart_image = Image(
                io.BytesIO(chart_png),
                width=6.5 * inch,
                height=3.8 * inch,
            )

            story.append(
                chart_image
            )

            story.append(
                Spacer(1, 20)
            )

        except Exception:

            story.append(
                Paragraph(
                    "The generated visualization "
                    "could not be embedded in the report.",
                    body_style,
                )
            )

            story.append(
                Spacer(1, 20)
            )

    # ========================================================
    # AI INSIGHTS
    # ========================================================

    story.append(
        Paragraph(
            "AI-Generated Insights",
            heading_style,
        )
    )

    if ai_insights:

        # Convert AI output to string
        insight_text = str(
            ai_insights
        )

        # Escape HTML-sensitive characters
        insight_text = (
            insight_text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        # Split AI output into paragraphs
        for paragraph in insight_text.split("\n"):

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            # Basic Markdown heading handling
            if paragraph.startswith("### "):

                heading_text = paragraph[4:]

                story.append(
                    Paragraph(
                        heading_text,
                        heading_style,
                    )
                )

            elif paragraph.startswith("## "):

                heading_text = paragraph[3:]

                story.append(
                    Paragraph(
                        heading_text,
                        heading_style,
                    )
                )

            elif paragraph.startswith("# "):

                heading_text = paragraph[2:]

                story.append(
                    Paragraph(
                        heading_text,
                        heading_style,
                    )
                )

            else:

                story.append(
                    Paragraph(
                        paragraph,
                        body_style,
                    )
                )

            story.append(
                Spacer(1, 5)
            )

    else:

        story.append(
            Paragraph(
                "No AI insights were available.",
                body_style,
            )
        )

    story.append(
        Spacer(1, 20)
    )

    # ========================================================
    # FINAL NOTE
    # ========================================================

    story.append(
        Paragraph(
            "Generated by DataMind AI",
            heading_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    story.append(
        Paragraph(
            "This report is intended to support "
            "data exploration and decision-making. "
            "Business decisions should be validated "
            "against the underlying data.",
            body_style,
        )
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()