from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series


OTTAWA_GEO = "Ottawa-Gatineau, Ontario part, Ontario/Quebec"
SOURCE_TABLE = "34100133"


class CMHCRentDataFrame(pa.DataFrameModel):
    reference_year: Series[int] = pa.Field(
        nullable=False,
        ge=1980,
    )
    geography: Series[str] = pa.Field(nullable=False)
    structure_type: Series[str] = pa.Field(nullable=False)
    unit_type: Series[str] = pa.Field(nullable=False)
    rent_value: Series[float] = pa.Field(nullable=False, gt=0)
    vector: Series[str] = pa.Field(nullable=False)
    source: Series[str] = pa.Field(isin=["cmhc"])

    class Config:
        strict = True
        coerce = True


def read_cmhc_csv(raw_path: Path) -> pd.DataFrame:
    """Read and lightly standardize the rental CSV inside the raw ZIP."""
    with ZipFile(raw_path) as archive:
        csv_name = f"{SOURCE_TABLE}.csv"
        if csv_name not in archive.namelist():
            raise ValueError(f"CMHC ZIP does not contain {csv_name}")

        dataframe = pd.read_csv(
            archive.open(csv_name),
            low_memory=False,
        )

    required_columns = {
        "REF_DATE",
        "GEO",
        "Type of structure",
        "Type of unit",
        "VALUE",
        "VECTOR",
    }
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(
            f"CMHC CSV is missing columns: {sorted(missing_columns)}"
        )

    dataframe = dataframe.loc[
        dataframe["GEO"].eq(OTTAWA_GEO)
        & dataframe["UOM"].eq("Dollars")
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
            "Type of structure": "structure_type",
            "Type of unit": "unit_type",
            "VALUE": "rent_value",
            "VECTOR": "vector",
        }
    )[
        [
            "reference_year",
            "geography",
            "structure_type",
            "unit_type",
            "rent_value",
            "vector",
        ]
    ].assign(source="cmhc")


def build_bronze_cmhc(
    raw_path: Path,
    bronze_path: Path,
) -> pd.DataFrame:
    """Read, validate, and write the Ottawa CMHC bronze dataset."""
    dataframe = read_cmhc_csv(raw_path)
    dataframe["reference_year"] = pd.to_numeric(
        dataframe["reference_year"]
    )
    dataframe["rent_value"] = pd.to_numeric(
        dataframe["rent_value"]
    )
    dataframe = dataframe.sort_values(
        ["reference_year", "structure_type", "unit_type"]
    )

    validated_dataframe = CMHCRentDataFrame.validate(dataframe)

    bronze_path.parent.mkdir(parents=True, exist_ok=True)
    validated_dataframe.to_parquet(bronze_path, index=False)

    return validated_dataframe


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    raw_path = (
        repo_root
        / "data"
        / "raw"
        / "cmhc"
        / "rental_market"
        / f"{SOURCE_TABLE}-eng.zip"
    )
    bronze_path = (
        repo_root
        / "data"
        / "bronze"
        / "cmhc"
        / "rental_market"
        / "rents.parquet"
    )

    result = build_bronze_cmhc(raw_path, bronze_path)
    print(f"Wrote {len(result)} CMHC rental rows to {bronze_path}")
