import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def get_numeric_columns(df):
    """Return numerical columns."""
    return df.select_dtypes(include="number").columns.tolist()


def get_categorical_columns(df):
    """Return categorical columns."""
    return df.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()


def create_histogram(df, column):
    """Create histogram for numerical column."""

    fig = px.histogram(
        df,
        x=column,
        title=f"Distribution of {column}",
        marginal="box",
        hover_data=df.columns
    )

    fig.update_layout(
        template="plotly_white",
        height=500
    )

    return fig


def create_box_plot(df, column):
    """Create box plot for numerical column."""

    fig = px.box(
        df,
        y=column,
        title=f"Box Plot — {column}"
    )

    fig.update_layout(
        template="plotly_white",
        height=500
    )

    return fig


def create_bar_chart(df, column):
    """Create bar chart for categorical column."""

    counts = (
        df[column]
        .value_counts()
        .head(10)
        .reset_index()
    )

    counts.columns = [column, "Count"]

    fig = px.bar(
        counts,
        x=column,
        y="Count",
        title=f"Top Categories — {column}",
        text="Count"
    )

    fig.update_layout(
        template="plotly_white",
        height=500
    )

    return fig


def create_scatter_plot(df, x_column, y_column):
    """Create scatter plot between two numerical columns."""

    fig = px.scatter(
        df,
        x=x_column,
        y=y_column,
        title=f"{y_column} vs {x_column}",
        trendline="ols"
    )

    fig.update_layout(
        template="plotly_white",
        height=500
    )

    return fig


def create_correlation_heatmap(df):
    """Create correlation heatmap."""

    numeric_df = df.select_dtypes(
        include="number"
    )

    if numeric_df.shape[1] < 2:
        return None

    correlation = numeric_df.corr()

    fig = px.imshow(
        correlation,
        text_auto=".2f",
        aspect="auto",
        title="Correlation Heatmap"
    )

    fig.update_layout(
        template="plotly_white",
        height=600
    )

    return fig