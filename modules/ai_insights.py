import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from google import genai


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def create_dataset_profile(df):

    profile = {}

    profile["rows"] = int(df.shape[0])

    profile["columns"] = int(df.shape[1])

    profile["column_names"] = df.columns.tolist()

    profile["data_types"] = {
        column: str(dtype)
        for column, dtype in df.dtypes.items()
    }

    profile["missing_values"] = (
        df.isnull()
        .sum()
        .sort_values(ascending=False)
        .head(15)
        .to_dict()
    )

    profile["duplicate_rows"] = int(
        df.duplicated().sum()
    )

    numeric_df = df.select_dtypes(
        include="number"
    )

    if not numeric_df.empty:

        profile["numeric_summary"] = (
            numeric_df
            .describe()
            .round(2)
            .to_dict()
        )

        if numeric_df.shape[1] >= 2:

            profile["correlations"] = (
                numeric_df
                .corr()
                .round(2)
                .to_dict()
            )

    categorical_columns = df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns

    profile["categorical_summary"] = {}

    for column in categorical_columns[:10]:

        profile["categorical_summary"][column] = (
            df[column]
            .value_counts()
            .head(10)
            .to_dict()
        )

    return profile


def generate_ai_insights(df):

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:

        return (
            " **Gemini API key not found.**\n\n"
            "Please check your `.env` file."
        )


    try:

        client = genai.Client(
            api_key=api_key
        )


        profile = create_dataset_profile(df)


        prompt = f"""
You are an expert Data Analyst and Business Intelligence consultant.

Analyze the following dataset profile.

DATASET PROFILE:

{profile}


Provide the analysis using these sections:

##  Executive Summary

Give a concise overview of the dataset.


##  Key Findings

Identify 3 to 5 important findings.

Use actual numbers whenever possible.


##  Trends & Relationships

Explain important relationships, correlations,
distributions, or category patterns.


##  Data Quality Concerns

Identify missing values, duplicate records,
or other data-quality issues.


##  Business Recommendations

Give 3 practical recommendations based strictly
on the available evidence.


##  Analyst Takeaway

Give a short final conclusion.


IMPORTANT RULES:

1. Do not invent information.
2. Use only the supplied dataset profile.
3. Do not claim correlation means causation.
4. If there is insufficient evidence, say so.
5. Use simple professional language.
6. Focus on actionable insights.
"""


        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )


        return response.text


    except Exception as e:

        return (
            " **Gemini API Error**\n\n"
            f"Error: {str(e)}\n\n"
            "Please check your API configuration "
            "and model availability."
        )
def answer_pdf_question(
    question,
    relevant_chunks
):

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        return {
            "answer": (
                " Gemini API key not found."
            ),
            "sources": []
        }


    if not relevant_chunks:

        return {
            "answer": (
                "I couldn't find relevant "
                "information in the uploaded PDF."
            ),
            "sources": []
        }


    try:

        client = genai.Client(
            api_key=api_key
        )


        context_parts = []

        sources = []


        for chunk in relevant_chunks:

            context_parts.append(
                f"""
PAGE {chunk['page']}:

{chunk['text']}
"""
            )

            if chunk["page"] not in sources:

                sources.append(
                    chunk["page"]
                )


        context = "\n\n".join(
            context_parts
        )


        prompt = f"""
You are DataMind AI, an expert document
analysis assistant.

Answer the user's question using ONLY
the information provided in the PDF context.

USER QUESTION:

{question}


PDF CONTEXT:

{context}


RULES:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not present in the context,
   clearly say that it was not found.
4. Give a concise but useful answer.
5. Mention important numbers when available.
6. Do not claim something that the document
   does not support.
"""


        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )


        return {
            "answer": response.text,
            "sources": sources
        }


    except Exception as e:

        return {
            "answer": (
                " Gemini API Error\n\n"
                + str(e)
            ),
            "sources": []
        }