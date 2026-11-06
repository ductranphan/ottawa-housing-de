from zipfile import ZipFile

import pandas as pd
import pandera.pandas as pa
import pytest

from dagster_project.dagster_project.ingestion.bronze_cmhc import (
    OTTAWA_GEO,
    SOURCE_TABLE,
    build_bronze_cmhc,
    read_cmhc_csv,
)


def write_sample_cmhc_zip(path, rent_values=None):
    if rent_values is None:
        rent_values = [1200, 1500]

    dataframe = pd.DataFrame(
        {
            "REF_DATE": [2023, 2024],
            "GEO": [OTTAWA_GEO, OTTAWA_GEO],
            "DGUID": ["x", "x"],
            "Type of structure": [
                "Apartment structures of three units and over",
                "Apartment structures of three units and over",
            ],
            "Type of unit": ["Bachelor units", "Bachelor units"],
            "UOM": ["Dollars", "Dollars"],
            "VALUE": rent_values,
            "VECTOR": ["v1", "v1"],
        }
    )

    with ZipFile(path, "w") as archive:
        with archive.open(f"{SOURCE_TABLE}.csv", "w") as csv_file:
            dataframe.to_csv(csv_file, index=False)


def test_read_cmhc_csv_filters_and_renames_data(tmp_path):
    raw_path = tmp_path / "cmhc.zip"
    write_sample_cmhc_zip(raw_path)

    dataframe = read_cmhc_csv(raw_path)

    assert len(dataframe) == 2
    assert dataframe["rent_value"].tolist() == [1200, 1500]
    assert "reference_year" in dataframe.columns
    assert dataframe["source"].eq("cmhc").all()


def test_build_bronze_cmhc_writes_parquet(tmp_path):
    raw_path = tmp_path / "cmhc.zip"
    bronze_path = tmp_path / "rents.parquet"
    write_sample_cmhc_zip(raw_path)

    result = build_bronze_cmhc(raw_path, bronze_path)
    saved = pd.read_parquet(bronze_path)

    assert bronze_path.exists()
    assert len(result) == 2
    assert len(saved) == 2
    assert saved["reference_year"].tolist() == [2023, 2024]


def test_build_bronze_cmhc_rejects_nonpositive_rent(tmp_path):
    raw_path = tmp_path / "invalid_cmhc.zip"
    bronze_path = tmp_path / "rents.parquet"
    write_sample_cmhc_zip(raw_path, rent_values=[-1, 1500])

    with pytest.raises(pa.errors.SchemaError):
        build_bronze_cmhc(raw_path, bronze_path)
