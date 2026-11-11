from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series


OTTAWA_GEO = "Ottawa-Gatineau, Ontario/Quebec"
SOURCE_TABLE = "11100238"


class IncomeDataFrame(pa.DataFrameModel):
    reference_year: Series[int] = pa.Field(nullable=False, ge=1976)
    geography: Series[str] = pa.Field(nullable=False)
    income_concept: Series[str] = pa.Field(nullable=False)
    statistic: Series[str] = pa.Field(nullable=False)
    income_value: Series[float] = pa.Field(nullable=False, ge=0)
    unit: Series[str] = pa.Field(nullable=False)
    vector: Series[str] = pa.Field(nullable=False)
    source: Series[str] = pa.Field(isin=["statcan"])

    class Config:
        strict = True
        coerce = True


def read_income_csv(raw_path: Path) -> pd.DataFrame:
    """Read and filter median after-tax income for Ottawa-Gatineau."""
    with ZipFile(raw_path) as archive:
        csv_name = f"{SOURCE_TABLE}.csv"
        if csv_name not in archive.namelist():
            raise ValueError(f"Income ZIP does not contain {csv_name}")

        dataframe = pd.read_csv(
            archive.open(csv_name),
            low_memory=False,
        )

    required_columns = {
        "REF_DATE",
        "GEO",
        "Income concept",
        "Statistics",
        "UOM",
        "VALUE",
        "VECTOR",
    }
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"Income CSV is missing columns: {sorted(missing_columns)}"
        )

    dataframe = dataframe.loc[
        dataframe["GEO"].eq(OTTAWA_GEO)
        & dataframe["Income concept"].eq("After-tax income")
        & dataframe["Statistics"].eq("Median income")
        & dataframe["UOM"].eq("2024 constant dollars")
    ].copy()
    dataframe["VALUE"] = pd.to_numeric(
        dataframe["VALUE"],
        errors="coerce",
    )
    dataframe = dataframe.dropna(subset=["VALUE"])

    return dataframe.rename(
        columns={
            "REF_DATE": "reference_year",
            "GEO": "geography",
            "Income concept": "income_concept",
            "Statistics": "statistic",
            "VALUE": "income_value",
            "UOM": "unit",
            "VECTOR": "vector",
        }
    )[
        [
            "reference_year",
            "geography",
            "income_concept",
            "statistic",
            "income_value",
            "unit",
            "vector",
        ]
    ].assign(source="statcan")


def build_bronze_income(
    raw_path: Path,
    bronze_path: Path,
) -> pd.DataFrame:
    """Read, validate, and write the income bronze dataset."""
    dataframe = read_income_csv(raw_path)
    dataframe["reference_year"] = pd.to_numeric(
        dataframe["reference_year"]
    )
    dataframe["income_value"] = pd.to_numeric(
        dataframe["income_value"]
    )
    dataframe = dataframe.sort_values("reference_year")

    validated_dataframe = IncomeDataFrame.validate(dataframe)

    bronze_path.parent.mkdir(parents=True, exist_ok=True)
    validated_dataframe.to_parquet(bronze_path, index=False)

    return validated_dataframe


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    raw_path = (
        repo_root
        / "data"
        / "raw"
        / "statcan"
        / "income"
        / f"{SOURCE_TABLE}-eng.zip"
    )
    bronze_path = (
        repo_root
        / "data"
        / "bronze"
        / "statcan"
        / "income"
        / "income.parquet"
    )

    result = build_bronze_income(raw_path, bronze_path)
    print(f"Wrote {len(result)} income rows to {bronze_path}")
