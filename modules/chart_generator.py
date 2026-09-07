import pandas as pd
import matplotlib.pyplot as plt


def generate_chart(
    df,
    chart_type,
    x_column,
    y_column=None
):
    """
    Generate a chart from the dataset.
    Returns a matplotlib Figure.
    """

    if x_column not in df.columns:
        raise ValueError(
            f"Column '{x_column}' does not exist."
        )

    if (
        y_column
        and y_column not in df.columns
    ):
        raise ValueError(
            f"Column '{y_column}' does not exist."
        )

    fig, ax = plt.subplots(
        figsize=(10, 5)
    )

    # --------------------------------------------------------
    # BAR
    # --------------------------------------------------------

    if chart_type == "bar":

        if y_column:

            data = (
                df.groupby(x_column)[y_column]
                .sum()
                .sort_values(
                    ascending=False
                )
                .head(15)
            )

            data.plot(
                kind="bar",
                ax=ax
            )

            ax.set_xlabel(x_column)
            ax.set_ylabel(y_column)

        else:

            counts = (
                df[x_column]
                .value_counts()
                .head(15)
            )

            counts.plot(
                kind="bar",
                ax=ax
            )

            ax.set_xlabel(x_column)
            ax.set_ylabel("Count")

    # --------------------------------------------------------
    # LINE
    # --------------------------------------------------------

    elif chart_type == "line":

        if not y_column:
            raise ValueError(
                "Line charts require a Y-axis column."
            )

        data = df[
            [x_column, y_column]
        ].dropna()

        data = data.sort_values(
            by=x_column
        )

        ax.plot(
            data[x_column],
            data[y_column]
        )

        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)

    # --------------------------------------------------------
    # SCATTER
    # --------------------------------------------------------

    elif chart_type == "scatter":

        if not y_column:
            raise ValueError(
                "Scatter plots require a Y-axis column."
            )

        data = df[
            [x_column, y_column]
        ].dropna()

        ax.scatter(
            data[x_column],
            data[y_column],
            alpha=0.6
        )

        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)

    # --------------------------------------------------------
    # HISTOGRAM
    # --------------------------------------------------------

    elif chart_type == "histogram":

        data = pd.to_numeric(
            df[x_column],
            errors="coerce"
        ).dropna()

        ax.hist(
            data,
            bins=20
        )

        ax.set_xlabel(x_column)
        ax.set_ylabel("Frequency")

    # --------------------------------------------------------
    # PIE
    # --------------------------------------------------------

    elif chart_type == "pie":

        counts = (
            df[x_column]
            .value_counts()
            .head(10)
        )

        ax.pie(
            counts.values,
            labels=counts.index,
            autopct="%1.1f%%"
        )

        ax.set_title(
            f"{x_column} Distribution"
        )

    # --------------------------------------------------------
    # BOX
    # --------------------------------------------------------

    elif chart_type == "box":

        data = pd.to_numeric(
            df[x_column],
            errors="coerce"
        ).dropna()

        ax.boxplot(data)

        ax.set_ylabel(x_column)

    else:

        raise ValueError(
            f"Unsupported chart type: {chart_type}"
        )

    ax.set_title(
        f"{chart_type.title()} Chart"
    )

    fig.tight_layout()

    return fig