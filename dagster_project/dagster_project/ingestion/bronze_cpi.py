from pathlib import Path
import json
import pandas as pd

raw_path = Path("data/raw/bank_of_canada/cpi/bank_of_canada_cpi.json")

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


rows = read_cpi_json(raw_path)
cpi_df = pd.DataFrame(rows)

cpi_df["reference_date"] = pd.to_datetime(cpi_df["reference_date"])

cpi_df = cpi_df.sort_values("reference_date")

bronze_path = Path("data/bronze/bank_of_canada/cpi/cpi.parquet")

bronze_path.parent.mkdir(parents = True, exist_ok = True)
cpi_df.to_parquet(bronze_path, index = False)

