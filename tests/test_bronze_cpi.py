import json

import pandas as pd
import pandera.pandas as pa
import pytest

from dagster_project.dagster_project.ingestion.bronze_cpi import (
    build_bronze_cpi,
    read_cpi_json,
)


def write_sample_cpi_json(path):
    data = {
        "observations": [
            {
                "d": "2024-02-01",
                "V41690973": {"v": "158.8"},
            },
            {
                "d": "2024-01-01",
                "V41690973": {"v": "158.3"},
            },
        ]
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_read_cpi_json_extracts_all_observations(tmp_path):
    raw_path = tmp_path / "cpi.json"
    write_sample_cpi_json(raw_path)

    rows = read_cpi_json(raw_path)

    assert len(rows) == 2
    assert rows[0]["reference_date"] == "2024-02-01"
    assert rows[0]["cpi_value"] == 158.8


def test_build_bronze_cpi_writes_valid_parquet(tmp_path):
    raw_path = tmp_path / "cpi.json"
    bronze_path = tmp_path / "cpi.parquet"
    write_sample_cpi_json(raw_path)

    result = build_bronze_cpi(raw_path, bronze_path)
    saved = pd.read_parquet(bronze_path)

    assert bronze_path.exists()
    assert len(result) == 2
    assert list(saved.columns) == [
        "reference_date",
        "cpi_value",
        "series_id",
        "source",
    ]
    assert saved["reference_date"].is_monotonic_increasing
    assert saved["cpi_value"].tolist() == [158.3, 158.8]


def test_build_bronze_cpi_rejects_nonpositive_cpi(tmp_path):
    raw_path = tmp_path / "invalid_cpi.json"
    bronze_path = tmp_path / "cpi.parquet"
    data = {
        "observations": [
            {
                "d": "2024-01-01",
                "V41690973": {"v": "-1"},
            }
        ]
    }
    raw_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(pa.errors.SchemaError):
        build_bronze_cpi(raw_path, bronze_path)
