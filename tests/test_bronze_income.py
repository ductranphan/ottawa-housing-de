from zipfile import ZipFile

import pandas as pd
import pandera.pandas as pa
import pytest

from dagster_project.dagster_project.ingestion.bronze_income import (
    OTTAWA_GEO,
    SOURCE_TABLE,
    build_bronze_income,
    read_income_csv,
)


def write_sample_income_zip(path, income_values=None):
    if income_values is None:
        income_values = [42000, 43000]

    dataframe = pd.DataFrame(
        {
            "REF_DATE": [2022, 2023],
            "GEO": [OTTAWA_GEO, OTTAWA_GEO],
            "Income concept": ["After-tax income", "After-tax income"],
            "Statistics": ["Median income", "Median income"],
            "UOM": ["2024 constant dollars", "2024 constant dollars"],
            "VALUE": income_values,
            "VECTOR": ["v1", "v1"],
        }
    )

    with ZipFile(path, "w") as archive:
        with archive.open(f"{SOURCE_TABLE}.csv", "w") as csv_file:
            dataframe.to_csv(csv_file, index=False)


def test_read_income_csv_filters_and_renames_data(tmp_path):
    raw_path = tmp_path / "income.zip"
    write_sample_income_zip(raw_path)

    dataframe = read_income_csv(raw_path)

    assert len(dataframe) == 2
    assert dataframe["income_value"].tolist() == [42000, 43000]
    assert dataframe["source"].eq("statcan").all()


def test_build_bronze_income_writes_parquet(tmp_path):
    raw_path = tmp_path / "income.zip"
    bronze_path = tmp_path / "income.parquet"
    write_sample_income_zip(raw_path)

    result = build_bronze_income(raw_path, bronze_path)
    saved = pd.read_parquet(bronze_path)

    assert bronze_path.exists()
    assert len(result) == 2
    assert len(saved) == 2
    assert saved["reference_year"].tolist() == [2022, 2023]


def test_build_bronze_income_rejects_negative_income(tmp_path):
    raw_path = tmp_path / "invalid_income.zip"
    bronze_path = tmp_path / "income.parquet"
    write_sample_income_zip(raw_path, income_values=[-1, 43000])

    with pytest.raises(pa.errors.SchemaError):
        build_bronze_income(raw_path, bronze_path)
