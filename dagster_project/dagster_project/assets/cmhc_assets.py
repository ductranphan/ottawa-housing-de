from pathlib import Path

from dagster import AssetExecutionContext, asset

from ..ingestion.bronze_cmhc import build_bronze_cmhc
from ..ingestion.cmhc_client import download_cmhc_rents


@asset
def cmhc_rental_market_bronze(
    context: AssetExecutionContext,
) -> Path:
    """Download CMHC rents and materialize the validated bronze Parquet."""
    repo_root = Path(__file__).resolve().parents[3]

    raw_dir = repo_root / "data" / "raw" / "cmhc" / "rental_market"
    raw_path = download_cmhc_rents(raw_dir)

    bronze_path = (
        repo_root
        / "data"
        / "bronze"
        / "cmhc"
        / "rental_market"
        / "rents.parquet"
    )
    bronze_df = build_bronze_cmhc(raw_path, bronze_path)

    context.add_output_metadata(
        {
            "source": "CMHC Rental Market data",
            "table_id": "34100133",
            "geography": "Ottawa-Gatineau, Ontario part",
            "row_count": len(bronze_df),
            "output_path": str(bronze_path),
        }
    )
    context.log.info(
        f"Materialized {len(bronze_df)} CMHC rental rows to {bronze_path}"
    )

    return bronze_path
