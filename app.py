from flask import Flask, render_template, request, send_file
import pandas as pd
import os

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns

from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# FOLDERS
# =========================================================

UPLOAD_FOLDER = "uploads"
CHART_FOLDER = "static/charts"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHART_FOLDER, exist_ok=True)


# =========================================================
# HOME PAGE + DATASET ANALYSIS
# =========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        # =================================================
        # CHECK FILE
        # =================================================

        if "file" not in request.files:
            return "No file selected."

        file = request.files["file"]

        if file.filename == "":
            return "No file selected."

        if not file.filename.lower().endswith(".csv"):
            return "Please upload a CSV file."

        # =================================================
        # SAVE FILE
        # =================================================

        filepath = os.path.join(
            UPLOAD_FOLDER,
            file.filename
        )

        file.save(filepath)

        # =================================================
        # READ CSV
        # =================================================

        try:
            df = pd.read_csv(filepath)

        except Exception as e:
            return f"Error reading CSV file: {e}"

        # =================================================
        # BASIC DATASET INFORMATION
        # =================================================

        rows = df.shape[0]
        columns = df.shape[1]

        missing_values = int(
            df.isnull().sum().sum()
        )

        duplicate_rows = int(
            df.duplicated().sum()
        )

        column_names = list(df.columns)

        # =================================================
        # USER-FRIENDLY DATA TYPES
        # =================================================

        data_types = []

        for column in df.columns:

            dtype = df[column].dtype
            column_lower = column.lower().strip()

            # -------------------------------------------------
            # DATE / TIME
            # -------------------------------------------------

            if (
                "date" in column_lower
                or "time" in column_lower
                or "timestamp" in column_lower
            ):

                detected_type = "Date / Time"

            # -------------------------------------------------
            # BOOLEAN
            # -------------------------------------------------

            elif pd.api.types.is_bool_dtype(dtype):

                detected_type = "Boolean"

            # -------------------------------------------------
            # INTEGER
            # -------------------------------------------------

            elif pd.api.types.is_integer_dtype(dtype):

                detected_type = "Integer"

            # -------------------------------------------------
            # DECIMAL
            # -------------------------------------------------

            elif pd.api.types.is_float_dtype(dtype):

                detected_type = "Decimal"

            # -------------------------------------------------
            # TEXT
            #
            # CSV text columns are normally stored as object.
            # Explicitly treating object/string/category as Text
            # prevents them from appearing as "Other".
            # -------------------------------------------------

            elif (
                pd.api.types.is_object_dtype(dtype)
                or pd.api.types.is_string_dtype(dtype)
                or isinstance(dtype, pd.CategoricalDtype)
            ):

                detected_type = "Text"

            # -------------------------------------------------
            # OTHER
            # -------------------------------------------------

            else:

                detected_type = "Other"

            data_types.append({
                "name": column,
                "type": detected_type
            })

        # =================================================
        # MISSING VALUES BY COLUMN
        # =================================================

        missing_data = []

        for column in df.columns:

            missing_data.append({
                "name": column,
                "count": int(
                    df[column].isnull().sum()
                )
            })

        # =================================================
        # DATA PREVIEW
        # =================================================

        preview = df.head(5).to_html(
            classes="data-table",
            index=False
        )

        # =================================================
        # NUMERICAL COLUMNS
        # =================================================

        numeric_df = df.select_dtypes(
            include="number"
        )

        # =================================================
        # IDENTIFY ID-LIKE NUMERICAL COLUMNS
        # =================================================

        id_like_columns = []

        for column in numeric_df.columns:

            column_lower = column.lower().strip()

            if (
                column_lower == "id"
                or column_lower.endswith("_id")
                or column_lower.endswith("id")
                or column_lower.startswith("id_")
            ):

                id_like_columns.append(column)

        # =================================================
        # IDENTIFY DATE/TIME-LIKE COLUMNS
        # =================================================

        date_like_columns = []

        for column in df.columns:

            column_lower = column.lower().strip()

            if (
                "date" in column_lower
                or "time" in column_lower
                or "timestamp" in column_lower
            ):

                date_like_columns.append(column)

        # =================================================
        # MEANINGFUL NUMERICAL DATA
        # =================================================

        analysis_numeric_df = numeric_df.drop(
            columns=id_like_columns,
            errors="ignore"
        )

        analysis_numeric_df = analysis_numeric_df.drop(
            columns=date_like_columns,
            errors="ignore"
        )

        # =================================================
        # NUMERICAL STATISTICS
        # =================================================

        numeric_stats = []

        for column in analysis_numeric_df.columns:

            numeric_stats.append({
                "name": column,
                "mean": round(
                    float(
                        analysis_numeric_df[column].mean()
                    ),
                    2
                ),
                "min": round(
                    float(
                        analysis_numeric_df[column].min()
                    ),
                    2
                ),
                "max": round(
                    float(
                        analysis_numeric_df[column].max()
                    ),
                    2
                )
            })

        # =================================================
        # DETECT SPECIAL COLUMNS
        # =================================================

        pass_column = None
        hours_column = None
        return_column = None

        # =================================================
        # DETECT PASS COLUMN
        # =================================================

        for column in df.columns:

            column_lower = column.lower().strip()

            if column_lower in [
                "pass",
                "passed",
                "result"
            ]:

                pass_column = column
                break

        # =================================================
        # DETECT STUDY HOURS COLUMN
        # =================================================

        for column in df.columns:

            column_lower = column.lower().strip()

            if (
                "hour" in column_lower
                and "stud" in column_lower
            ):

                hours_column = column
                break

        # =================================================
        # DETECT RETURN STATUS COLUMN
        # =================================================

        for column in df.columns:

            column_lower = column.lower().strip()

            if (
                "return" in column_lower
                and "status" in column_lower
            ):

                return_column = column
                break

        # =================================================
        # CATEGORICAL COLUMNS
        # =================================================

        categorical_columns = df.select_dtypes(
            exclude="number"
        ).columns

        # =================================================
        # AUTOMATIC INSIGHTS
        # =================================================

        insights = []

        # =================================================
        # DATASET SIZE
        # =================================================

        insights.append(
            f"The dataset contains {rows} rows "
            f"and {columns} columns."
        )

        # =================================================
        # MISSING VALUES
        # =================================================

        if missing_values == 0:

            insights.append(
                "The dataset does not contain "
                "any missing values."
            )

        else:

            insights.append(
                f"The dataset contains "
                f"{missing_values} missing values."
            )

        # =================================================
        # DUPLICATES
        # =================================================

        if duplicate_rows == 0:

            insights.append(
                "No duplicate rows were detected."
            )

        else:

            insights.append(
                f"{duplicate_rows} duplicate rows "
                f"were detected."
            )

        # =================================================
        # NUMERICAL INSIGHTS
        # =================================================

        for column in analysis_numeric_df.columns:

            mean_value = (
                analysis_numeric_df[column].mean()
            )

            min_value = (
                analysis_numeric_df[column].min()
            )

            max_value = (
                analysis_numeric_df[column].max()
            )

            insights.append(
                f"{column} has an average value of "
                f"{mean_value:.2f}, with values ranging "
                f"from {min_value:.2f} to {max_value:.2f}."
            )

        # =================================================
        # STUDENT PERFORMANCE ANALYSIS
        # =================================================

        if pass_column is not None:

            try:

                pass_values = pd.to_numeric(
                    df[pass_column],
                    errors="coerce"
                )

                valid_pass = pass_values.dropna()

                if len(valid_pass) > 0:

                    unique_values = set(
                        valid_pass.unique()
                    )

                    if unique_values.issubset({0, 1}):

                        pass_rate = (
                            valid_pass.mean() * 100
                        )

                        insights.append(
                            f"The student pass rate is "
                            f"{pass_rate:.1f}%."
                        )

                        if pass_rate >= 75:

                            insights.append(
                                "Overall student performance "
                                "is relatively strong."
                            )

                        elif pass_rate >= 50:

                            insights.append(
                                "Student performance is moderate "
                                "and may require improvement."
                            )

                        else:

                            insights.append(
                                "The pass rate is low and indicates "
                                "a need for improved academic support."
                            )

            except Exception:
                pass

        # =================================================
        # STUDY HOURS ANALYSIS
        # =================================================

        if (
            pass_column is not None
            and hours_column is not None
        ):

            try:

                temp_df = df[
                    [
                        hours_column,
                        pass_column
                    ]
                ].copy()

                temp_df[hours_column] = pd.to_numeric(
                    temp_df[hours_column],
                    errors="coerce"
                )

                temp_df[pass_column] = pd.to_numeric(
                    temp_df[pass_column],
                    errors="coerce"
                )

                passed_hours = temp_df[
                    temp_df[pass_column] == 1
                ][hours_column].mean()

                failed_hours = temp_df[
                    temp_df[pass_column] == 0
                ][hours_column].mean()

                if (
                    pd.notna(passed_hours)
                    and pd.notna(failed_hours)
                ):

                    insights.append(
                        f"Students who passed studied an "
                        f"average of {passed_hours:.2f} hours, "
                        f"while students who failed studied "
                        f"an average of {failed_hours:.2f} hours."
                    )

            except Exception:
                pass

        # =================================================
        # RETURN RATE ANALYSIS
        # =================================================

        if return_column is not None:

            try:

                normalized = (
                    df[return_column]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                returned_values = [
                    "returned",
                    "return",
                    "yes",
                    "1"
                ]

                returned_count = normalized.isin(
                    returned_values
                ).sum()

                return_rate = (
                    returned_count / rows * 100
                    if rows > 0
                    else 0
                )

                insights.append(
                    f"The overall return rate is "
                    f"{return_rate:.1f}%."
                )

            except Exception:
                pass

        # =================================================
        # CATEGORICAL INSIGHTS
        # =================================================

        for column in categorical_columns:

            unique_count = df[column].nunique()

            if (
                rows > 0
                and unique_count >= rows * 0.9
            ):

                continue

            if unique_count > 0:

                try:

                    counts = df[
                        column
                    ].value_counts(
                        dropna=True
                    )

                    most_common = counts.idxmax()

                    most_common_count = counts.max()

                    insights.append(
                        f"The most common value in "
                        f"{column} is '{most_common}', "
                        f"appearing {most_common_count} times."
                    )

                except Exception:
                    pass

        # =================================================
        # STRONGEST CORRELATION
        # =================================================

        strongest_value = None
        strongest_pair = None

        if len(
            analysis_numeric_df.columns
        ) >= 2:

            try:

                correlation_matrix = (
                    analysis_numeric_df.corr()
                )

                max_corr = 0

                for i in range(
                    len(
                        correlation_matrix.columns
                    )
                ):

                    for j in range(
                        i + 1,
                        len(
                            correlation_matrix.columns
                        )
                    ):

                        value = correlation_matrix.iloc[
                            i,
                            j
                        ]

                        if (
                            pd.notna(value)
                            and abs(value) > abs(max_corr)
                        ):

                            max_corr = value

                            strongest_pair = (
                                correlation_matrix.columns[i],
                                correlation_matrix.columns[j]
                            )

                if strongest_pair is not None:

                    strongest_value = max_corr

                    insights.append(
                        f"The strongest numerical correlation "
                        f"is {max_corr:.2f} between "
                        f"{strongest_pair[0]} and "
                        f"{strongest_pair[1]}."
                    )

            except Exception:
                pass

        # =================================================
        # INTELLIGENT RECOMMENDATIONS
        # =================================================

        recommendations = []

        # =================================================
        # DATA QUALITY
        # =================================================

        if missing_values > 0:

            recommendations.append(
                f"Review the {missing_values} missing values "
                "before performing advanced analysis or "
                "building predictive models."
            )

        else:

            recommendations.append(
                "The dataset has no missing values, "
                "indicating good data completeness."
            )

        # =================================================
        # DUPLICATES
        # =================================================

        if duplicate_rows > 0:

            recommendations.append(
                f"Investigate and remove the {duplicate_rows} "
                "duplicate records to maintain data accuracy."
            )

        else:

            recommendations.append(
                "No duplicate records were detected, "
                "supporting reliable analysis."
            )

        # =================================================
        # NUMERICAL RELATIONSHIP
        # =================================================

        if (
            strongest_pair is not None
            and strongest_value is not None
        ):

            column_1 = strongest_pair[0]
            column_2 = strongest_pair[1]
            correlation_value = strongest_value

            if abs(correlation_value) >= 0.70:

                relationship = "strong"

            elif abs(correlation_value) >= 0.40:

                relationship = "moderate"

            else:

                relationship = "weak"

            recommendations.append(
                f"{column_1} and {column_2} show a "
                f"{relationship} relationship "
                f"(correlation: {correlation_value:.2f}). "
                "Consider investigating the business factors "
                "behind this relationship."
            )

        # =================================================
        # CATEGORICAL DATA
        # =================================================

        for column in categorical_columns:

            unique_count = df[column].nunique()

            if (
                rows > 0
                and unique_count >= rows * 0.9
            ):

                continue

            if 2 <= unique_count <= 10:

                try:

                    counts = (
                        df[column]
                        .value_counts(
                            dropna=True
                        )
                    )

                    if len(counts) > 0:

                        top_category = counts.index[0]

                        top_count = counts.iloc[0]

                        percentage = (
                            top_count / rows * 100
                            if rows > 0
                            else 0
                        )

                        if percentage >= 40:

                            recommendations.append(
                                f"'{top_category}' is the dominant "
                                f"category in {column}, representing "
                                f"{percentage:.1f}% of records. "
                                "Consider examining why this category "
                                "has such a high concentration."
                            )

                except Exception:
                    pass

                break

        # =================================================
        # STUDENT PERFORMANCE
        # =================================================

        if (
            pass_column is not None
            and hours_column is not None
        ):

            try:

                temp_df = df[
                    [
                        hours_column,
                        pass_column
                    ]
                ].copy()

                temp_df[hours_column] = pd.to_numeric(
                    temp_df[hours_column],
                    errors="coerce"
                )

                temp_df[pass_column] = pd.to_numeric(
                    temp_df[pass_column],
                    errors="coerce"
                )

                temp_df = temp_df.dropna()

                passed = temp_df[
                    temp_df[pass_column] == 1
                ]

                failed = temp_df[
                    temp_df[pass_column] == 0
                ]

                if (
                    len(passed) > 0
                    and len(failed) > 0
                ):

                    passed_hours = passed[
                        hours_column
                    ].mean()

                    failed_hours = failed[
                        hours_column
                    ].mean()

                    difference = (
                        passed_hours
                        - failed_hours
                    )

                    if difference > 0:

                        recommendations.append(
                            f"Passed students studied approximately "
                            f"{difference:.2f} more hours on average "
                            "than failed students. Encourage consistent "
                            "study schedules and targeted academic support."
                        )

            except Exception:
                pass

        # =================================================
        # E-COMMERCE RETURN ANALYSIS
        # =================================================

        if return_column is not None:

            try:

                normalized = (
                    df[return_column]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                returned_values = [
                    "returned",
                    "return",
                    "yes",
                    "1"
                ]

                returned_count = normalized.isin(
                    returned_values
                ).sum()

                return_rate = (
                    returned_count / rows * 100
                    if rows > 0
                    else 0
                )

                if return_rate >= 30:

                    recommendations.append(
                        f"The return rate is {return_rate:.1f}%, "
                        "which is relatively high. Investigate return "
                        "reasons, product quality, and customer expectations."
                    )

                elif return_rate >= 15:

                    recommendations.append(
                        f"The return rate is {return_rate:.1f}%. "
                        "Monitor return reasons and identify categories "
                        "with unusually high return activity."
                    )

                else:

                    recommendations.append(
                        f"The return rate is {return_rate:.1f}%, "
                        "indicating comparatively lower return activity."
                    )

            except Exception:
                pass

        # =================================================
        # GENERAL DATA RECOMMENDATION
        # =================================================

        if len(
            analysis_numeric_df.columns
        ) > 0:

            recommendations.append(
                "Track the key numerical metrics over time "
                "to identify emerging trends and support "
                "data-driven decisions."
            )

        else:

            recommendations.append(
                "Focus on categorical distributions and data "
                "quality patterns to identify important segments "
                "within the dataset."
            )

        # =================================================
        # DELETE OLD CHARTS
        # =================================================

        for old_chart in os.listdir(
            CHART_FOLDER
        ):

            old_chart_path = os.path.join(
                CHART_FOLDER,
                old_chart
            )

            if os.path.isfile(
                old_chart_path
            ):

                try:
                    os.remove(old_chart_path)

                except Exception:
                    pass

        # =================================================
        # CHART LIST
        # =================================================

        charts = []

        # =================================================
        # 1. STUDY HOURS VS PASS
        # =================================================

        if (
            pass_column is not None
            and hours_column is not None
        ):

            try:

                chart_df = df[
                    [
                        hours_column,
                        pass_column
                    ]
                ].copy()

                chart_df[hours_column] = pd.to_numeric(
                    chart_df[hours_column],
                    errors="coerce"
                )

                chart_df[pass_column] = pd.to_numeric(
                    chart_df[pass_column],
                    errors="coerce"
                )

                chart_df = chart_df.dropna()

                if len(chart_df) > 0:

                    plt.figure(
                        figsize=(8, 5)
                    )

                    sns.scatterplot(
                        data=chart_df,
                        x=hours_column,
                        y=pass_column
                    )

                    plt.title(
                        "Study Hours vs Pass Status"
                    )

                    plt.xlabel(
                        hours_column
                    )

                    plt.ylabel(
                        pass_column
                    )

                    plt.tight_layout()

                    chart_name = (
                        "study_hours_vs_pass.png"
                    )

                    chart_path = os.path.join(
                        CHART_FOLDER,
                        chart_name
                    )

                    plt.savefig(
                        chart_path,
                        dpi=150,
                        bbox_inches="tight"
                    )

                    plt.close()

                    charts.append(
                        chart_name
                    )

            except Exception:
                pass

        # =================================================
        # 2. PASS DISTRIBUTION
        # =================================================

        elif pass_column is not None:

            try:

                plt.figure(
                    figsize=(8, 5)
                )

                pass_counts = (
                    df[pass_column]
                    .value_counts()
                    .sort_index()
                )

                pass_counts.plot(
                    kind="bar"
                )

                plt.title(
                    "Pass / Fail Distribution"
                )

                plt.xlabel(
                    pass_column
                )

                plt.ylabel(
                    "Number of Students"
                )

                plt.xticks(
                    rotation=0
                )

                plt.tight_layout()

                chart_name = (
                    "pass_distribution.png"
                )

                chart_path = os.path.join(
                    CHART_FOLDER,
                    chart_name
                )

                plt.savefig(
                    chart_path,
                    dpi=150,
                    bbox_inches="tight"
                )

                plt.close()

                charts.append(
                    chart_name
                )

            except Exception:
                pass

        # =================================================
        # 3. STRONGEST NUMERICAL RELATIONSHIP
        # =================================================

        elif (
            len(
                analysis_numeric_df.columns
            ) >= 2
            and strongest_pair is not None
        ):

            try:

                x_column = strongest_pair[0]
                y_column = strongest_pair[1]

                chart_df = analysis_numeric_df[
                    [
                        x_column,
                        y_column
                    ]
                ].dropna()

                if len(chart_df) > 1:

                    plt.figure(
                        figsize=(8, 5)
                    )

                    sns.scatterplot(
                        data=chart_df,
                        x=x_column,
                        y=y_column
                    )

                    plt.title(
                        f"{x_column} vs {y_column}"
                    )

                    plt.xlabel(
                        x_column
                    )

                    plt.ylabel(
                        y_column
                    )

                    plt.tight_layout()

                    chart_name = (
                        "strongest_relationship.png"
                    )

                    chart_path = os.path.join(
                        CHART_FOLDER,
                        chart_name
                    )

                    plt.savefig(
                        chart_path,
                        dpi=150,
                        bbox_inches="tight"
                    )

                    plt.close()

                    charts.append(
                        chart_name
                    )

            except Exception:
                pass

        # =================================================
        # 4. GENERAL HISTOGRAM
        # =================================================

        elif (
            len(
                analysis_numeric_df.columns
            ) == 1
        ):

            try:

                first_numeric = (
                    analysis_numeric_df.columns[0]
                )

                values = analysis_numeric_df[
                    first_numeric
                ].dropna()

                if len(values) > 0:

                    plt.figure(
                        figsize=(8, 5)
                    )

                    plt.hist(
                        values,
                        bins=10
                    )

                    plt.title(
                        f"Distribution of {first_numeric}"
                    )

                    plt.xlabel(
                        first_numeric
                    )

                    plt.ylabel(
                        "Frequency"
                    )

                    plt.tight_layout()

                    chart_name = (
                        "histogram.png"
                    )

                    chart_path = os.path.join(
                        CHART_FOLDER,
                        chart_name
                    )

                    plt.savefig(
                        chart_path,
                        dpi=150,
                        bbox_inches="tight"
                    )

                    plt.close()

                    charts.append(
                        chart_name
                    )

            except Exception:
                pass

        # =================================================
        # 5. CORRELATION HEATMAP
        # =================================================

        if len(
            analysis_numeric_df.columns
        ) >= 2:

            try:

                correlation_matrix = (
                    analysis_numeric_df.corr()
                )

                plt.figure(
                    figsize=(8, 6)
                )

                sns.heatmap(
                    correlation_matrix,
                    annot=True,
                    cmap="coolwarm",
                    fmt=".2f",
                    linewidths=0.5
                )

                plt.title(
                    "Correlation Heatmap"
                )

                plt.tight_layout()

                chart_name = (
                    "correlation_heatmap.png"
                )

                chart_path = os.path.join(
                    CHART_FOLDER,
                    chart_name
                )

                plt.savefig(
                    chart_path,
                    dpi=150,
                    bbox_inches="tight"
                )

                plt.close()

                charts.append(
                    chart_name
                )

            except Exception:
                pass

        # =================================================
        # 6. CATEGORICAL DISTRIBUTION
        # =================================================

        for column in categorical_columns:

            unique_count = df[column].nunique()

            if (
                rows > 0
                and unique_count >= rows * 0.9
            ):

                continue

            if 1 < unique_count <= 10:

                try:

                    category_counts = (
                        df[column]
                        .value_counts()
                        .head(10)
                    )

                    plt.figure(
                        figsize=(8, 5)
                    )

                    category_counts.plot(
                        kind="bar"
                    )

                    plt.title(
                        f"{column} Distribution"
                    )

                    plt.xlabel(
                        column
                    )

                    plt.ylabel(
                        "Count"
                    )

                    plt.xticks(
                        rotation=45,
                        ha="right"
                    )

                    plt.tight_layout()

                    chart_name = (
                        "categorical_distribution.png"
                    )

                    chart_path = os.path.join(
                        CHART_FOLDER,
                        chart_name
                    )

                    plt.savefig(
                        chart_path,
                        dpi=150,
                        bbox_inches="tight"
                    )

                    plt.close()

                    charts.append(
                        chart_name
                    )

                    break

                except Exception:
                    pass

        # =================================================
        # SAVE LATEST DATASET PATH
        # =================================================

        latest_file = os.path.join(
            UPLOAD_FOLDER,
            "latest_dataset.txt"
        )

        with open(
            latest_file,
            "w"
        ) as f:

            f.write(filepath)

        # =================================================
        # RENDER RESULTS
        # =================================================

        return render_template(
            "results.html",
            rows=rows,
            columns=columns,
            missing_values=missing_values,
            duplicate_rows=duplicate_rows,
            column_names=column_names,
            data_types=data_types,
            missing_data=missing_data,
            preview=preview,
            numeric_stats=numeric_stats,
            insights=insights,
            recommendations=recommendations,
            charts=charts
        )

    # =====================================================
    # GET REQUEST
    # =====================================================

    return render_template(
        "index.html"
    )


# =========================================================
# DOWNLOAD PDF REPORT
# =========================================================

@app.route("/download_report")
def download_report():

    # =====================================================
    # FIND LAST DATASET
    # =====================================================

    latest_file = os.path.join(
        UPLOAD_FOLDER,
        "latest_dataset.txt"
    )

    if not os.path.exists(
        latest_file
    ):

        return (
            "Please analyze a dataset first "
            "before downloading the report."
        )

    # =====================================================
    # READ DATASET PATH
    # =====================================================

    with open(
        latest_file,
        "r"
    ) as f:

        filepath = f.read().strip()

    if not os.path.exists(
        filepath
    ):

        return (
            "The analyzed dataset "
            "could not be found."
        )

    # =====================================================
    # READ DATASET
    # =====================================================

    try:

        df = pd.read_csv(
            filepath
        )

    except Exception as e:

        return f"Error reading dataset: {e}"

    # =====================================================
    # BASIC INFORMATION
    # =====================================================

    rows = df.shape[0]
    columns = df.shape[1]

    missing_values = int(
        df.isnull().sum().sum()
    )

    duplicate_rows = int(
        df.duplicated().sum()
    )

    # =====================================================
    # NUMERICAL COLUMNS
    # =====================================================

    numeric_df = df.select_dtypes(
        include="number"
    )

    # =====================================================
    # REMOVE ID-LIKE NUMERICAL COLUMNS
    # =====================================================

    id_like_columns = []

    for column in numeric_df.columns:

        column_lower = column.lower().strip()

        if (
            column_lower == "id"
            or column_lower.endswith("_id")
            or column_lower.endswith("id")
            or column_lower.startswith("id_")
        ):

            id_like_columns.append(
                column
            )

    numeric_df = numeric_df.drop(
        columns=id_like_columns,
        errors="ignore"
    )

    # =====================================================
    # REMOVE DATE/TIME-LIKE COLUMNS
    # =====================================================

    date_like_columns = []

    for column in df.columns:

        column_lower = column.lower().strip()

        if (
            "date" in column_lower
            or "time" in column_lower
            or "timestamp" in column_lower
        ):

            date_like_columns.append(
                column
            )

    numeric_df = numeric_df.drop(
        columns=date_like_columns,
        errors="ignore"
    )

    # =====================================================
    # PDF PATH
    # =====================================================

    report_path = os.path.join(
        UPLOAD_FOLDER,
        "analysis_report.pdf"
    )

    # =====================================================
    # CREATE PDF
    # =====================================================

    document = SimpleDocTemplate(
        report_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    # =====================================================
    # PDF STYLES
    # =====================================================

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]

    story = []

    # =====================================================
    # TITLE
    # =====================================================

    story.append(
        Paragraph(
            "Data Analysis Report",
            title_style
        )
    )

    story.append(
        Spacer(
            1,
            15
        )
    )

    story.append(
        Paragraph(
            "Automated Dataset Analysis using "
            "Python and Pandas",
            normal_style
        )
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    # =====================================================
    # DATASET SUMMARY
    # =====================================================

    story.append(
        Paragraph(
            "1. Dataset Summary",
            heading_style
        )
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    summary_data = [
        [
            "Metric",
            "Value"
        ],
        [
            "Total Rows",
            str(rows)
        ],
        [
            "Total Columns",
            str(columns)
        ],
        [
            "Missing Values",
            str(missing_values)
        ],
        [
            "Duplicate Rows",
            str(duplicate_rows)
        ]
    ]

    summary_table = Table(
        summary_data,
        colWidths=[
            250,
            150
        ]
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    # =====================================================
    # DATASET COLUMNS
    # =====================================================

    story.append(
        Paragraph(
            "2. Dataset Columns",
            heading_style
        )
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    column_data = [
        [
            "Column",
            "Data Type"
        ]
    ]

    for column in df.columns:

        dtype = df[column].dtype
        column_lower = column.lower().strip()

        if (
            "date" in column_lower
            or "time" in column_lower
            or "timestamp" in column_lower
        ):

            display_type = "Date / Time"

        elif pd.api.types.is_bool_dtype(dtype):

            display_type = "Boolean"

        elif pd.api.types.is_integer_dtype(dtype):

            display_type = "Integer"

        elif pd.api.types.is_float_dtype(dtype):

            display_type = "Decimal"

        elif (
            pd.api.types.is_object_dtype(dtype)
            or pd.api.types.is_string_dtype(dtype)
            or isinstance(dtype, pd.CategoricalDtype)
        ):

            display_type = "Text"

        else:

            display_type = "Other"

        column_data.append([
            str(column),
            display_type
        ])

    column_table = Table(
        column_data,
        colWidths=[
            250,
            150
        ]
    )

    column_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(
        column_table
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    # =====================================================
    # NUMERICAL STATISTICS
    # =====================================================

    if len(
        numeric_df.columns
    ) > 0:

        story.append(
            Paragraph(
                "3. Numerical Statistics",
                heading_style
            )
        )

        story.append(
            Spacer(
                1,
                8
            )
        )

        stats_data = [
            [
                "Column",
                "Mean",
                "Minimum",
                "Maximum"
            ]
        ]

        for column in numeric_df.columns:

            stats_data.append([
                str(column),
                f"{numeric_df[column].mean():.2f}",
                f"{numeric_df[column].min():.2f}",
                f"{numeric_df[column].max():.2f}"
            ])

        stats_table = Table(
            stats_data,
            colWidths=[
                160,
                80,
                80,
                80
            ]
        )

        stats_table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        story.append(
            stats_table
        )

        story.append(
            Spacer(
                1,
                20
            )
        )

    # =====================================================
    # AUTOMATIC INSIGHTS
    # =====================================================

    story.append(
        Paragraph(
            "4. Automatic Insights",
            heading_style
        )
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    report_insights = []

    report_insights.append(
        f"The dataset contains {rows} rows "
        f"and {columns} columns."
    )

    if missing_values == 0:

        report_insights.append(
            "No missing values were detected."
        )

    else:

        report_insights.append(
            f"The dataset contains "
            f"{missing_values} missing values."
        )

    if duplicate_rows == 0:

        report_insights.append(
            "No duplicate rows were detected."
        )

    else:

        report_insights.append(
            f"{duplicate_rows} duplicate rows "
            f"were detected."
        )

    # =====================================================
    # PDF CORRELATION
    # =====================================================

    if len(
        numeric_df.columns
    ) >= 2:

        try:

            correlation_matrix = numeric_df.corr()

            max_corr = 0
            pair = None

            for i in range(
                len(
                    correlation_matrix.columns
                )
            ):

                for j in range(
                    i + 1,
                    len(
                        correlation_matrix.columns
                    )
                ):

                    value = correlation_matrix.iloc[
                        i,
                        j
                    ]

                    if (
                        pd.notna(value)
                        and abs(value) > abs(max_corr)
                    ):

                        max_corr = value

                        pair = (
                            correlation_matrix.columns[i],
                            correlation_matrix.columns[j]
                        )

            if pair is not None:

                report_insights.append(
                    f"The strongest numerical correlation "
                    f"is {max_corr:.2f} between "
                    f"{pair[0]} and {pair[1]}."
                )

        except Exception:
            pass

    for insight in report_insights:

        story.append(
            Paragraph(
                "• " + insight,
                normal_style
            )
        )

        story.append(
            Spacer(
                1,
                5
            )
        )

    story.append(
        Spacer(
            1,
            15
        )
    )

    # =====================================================
    # PDF RECOMMENDATION
    # =====================================================

    story.append(
        Paragraph(
            "5. Recommendations",
            heading_style
        )
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    if missing_values > 0:

        recommendation = (
            f"Review the {missing_values} missing values "
            "before performing advanced analysis."
        )

    elif duplicate_rows > 0:

        recommendation = (
            f"Investigate the {duplicate_rows} duplicate "
            "records to improve data quality."
        )

    else:

        recommendation = (
            "The dataset has good basic data quality. "
            "Continue monitoring important metrics and trends."
        )

    story.append(
        Paragraph(
            "• " + recommendation,
            normal_style
        )
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    # =====================================================
    # VISUALIZATIONS
    # =====================================================

    story.append(
        Paragraph(
            "6. Visualizations",
            heading_style
        )
    )

    story.append(
        Spacer(
            1,
            8
        )
    )

    chart_files = [
        "study_hours_vs_pass.png",
        "pass_distribution.png",
        "strongest_relationship.png",
        "histogram.png",
        "correlation_heatmap.png",
        "categorical_distribution.png"
    ]

    for chart_name in chart_files:

        chart_path = os.path.join(
            CHART_FOLDER,
            chart_name
        )

        if os.path.exists(
            chart_path
        ):

            try:

                story.append(
                    Image(
                        chart_path,
                        width=6 * inch,
                        height=4 * inch
                    )
                )

                story.append(
                    Spacer(
                        1,
                        15
                    )
                )

            except Exception:
                pass

    # =====================================================
    # BUILD PDF
    # =====================================================

    try:

        document.build(
            story
        )

    except Exception as e:

        return (
            f"Error creating PDF report: {e}"
        )

    # =====================================================
    # DOWNLOAD
    # =====================================================

    return send_file(
        report_path,
        as_attachment=True,
        download_name="data_analysis_report.pdf"
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )