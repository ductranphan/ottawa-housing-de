from pathlib import Path
import json
import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

class CPIDataFrame(pa.DataFrameModel):
    reference_date: Series[pd.Timestamp] = pa.Field(
        nullable=False,
        unique=True,
    )

    cpi_value: Series[float] = pa.Field(
        nullable=False,
        gt = 0,
    )

    series_id: Series[str] = pa.Field(
        isin=["V41690973"],
    )

    source: Series[str] = pa.Field(
        isin=["bank_of_canada"],
    )

    class Config:
        strict = True
        coerce = True



def read_cpi_json(raw_path: Path) -> list[dict]:
    with raw_path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    if "observations" not in raw_data:
        raise ValueError("JSON does not contain observations")

    series_id = "V41690973"
    rows = []

    for observation in raw_data["observations"]:
        if "d" not in observation:
            raise ValueError("Observation is missing a date")

        if series_id not in observation:
            raise ValueError(f"Observation is missing {series_id}")

        value = observation[series_id].get("v")

        if value is None:
            raise ValueError("Observation is missing a CPI value")

        rows.append(
            {
                "reference_date": observation["d"],
                "cpi_value": float(value),
                "series_id": series_id,
                "source": "bank_of_canada",
            }
        )


    return rows


def build_bronze_cpi(
    raw_path: Path,
    bronze_path: Path,
) -> pd.DataFrame:
    """Read, validate, and write the Bank of Canada CPI bronze dataset."""
    rows = read_cpi_json(raw_path)
    cpi_df = pd.DataFrame(rows)

    cpi_df["reference_date"] = pd.to_datetime(
        cpi_df["reference_date"]
    )
    cpi_df["cpi_value"] = pd.to_numeric(
        cpi_df["cpi_value"]
    )
    cpi_df = cpi_df.sort_values("reference_date")

    validated_df = CPIDataFrame.validate(cpi_df)

    bronze_path.parent.mkdir(parents=True, exist_ok=True)
    validated_df.to_parquet(bronze_path, index=False)

    return validated_df


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[3]
    raw_path = (
        repo_root
        / "data"
        / "raw"
        / "bank_of_canada"
        / "cpi"
        / "bank_of_canada_cpi.json"
    )
    bronze_path = (
        repo_root
        / "data"
        / "bronze"
        / "bank_of_canada"
        / "cpi"
        / "cpi.parquet"
    )

    result = build_bronze_cpi(raw_path, bronze_path)
    print(f"Wrote {len(result)} rows to {bronze_path}")

