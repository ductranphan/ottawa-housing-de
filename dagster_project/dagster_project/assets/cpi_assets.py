from pathlib import Path

from dagster import AssetExecutionContext, asset

from ..ingestion.bankcan_client import download_cpi
from ..ingestion.bronze_cpi import build_bronze_cpi


@asset
def bank_of_canada_cpi_bronze(
    context: AssetExecutionContext,
) -> Path:
    """Download Bank of Canada CPI data and materialize its bronze Parquet file."""
    repo_root = Path(__file__).resolve().parents[3]

    raw_dir = (
        repo_root
        / "data"
        / "raw"
        / "bank_of_canada"
        / "cpi"
    )
    raw_path = download_cpi(raw_dir)

    bronze_path = (
        repo_root
        / "data"
        / "bronze"
        / "bank_of_canada"
        / "cpi"
        / "cpi.parquet"
    )
    bronze_df = build_bronze_cpi(raw_path, bronze_path)

    context.add_output_metadata(
        {
            "source": "Bank of Canada Valet API",
            "row_count": len(bronze_df),
            "output_path": str(bronze_path),
        }
    )
    context.log.info(
        f"Materialized {len(bronze_df)} CPI rows to {bronze_path}"
    )

    return bronze_path
