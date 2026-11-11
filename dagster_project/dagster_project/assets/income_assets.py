from pathlib import Path

from dagster import AssetExecutionContext, asset

from ..ingestion.bronze_income import build_bronze_income
from ..ingestion.income_client import download_income


@asset
def statcan_income_bronze(
    context: AssetExecutionContext,
) -> Path:
    """Download StatCan income data and materialize validated bronze Parquet."""
    repo_root = Path(__file__).resolve().parents[3]

    raw_dir = repo_root / "data" / "raw" / "statcan" / "income"
    raw_path = download_income(raw_dir)

    bronze_path = (
        repo_root
        / "data"
        / "bronze"
        / "statcan"
        / "income"
        / "income.parquet"
    )
    income_df = build_bronze_income(raw_path, bronze_path)

    context.add_output_metadata(
        {
            "source": "Statistics Canada",
            "table_id": "11100238",
            "geography": "Ottawa-Gatineau, Ontario/Quebec",
            "income_measure": "Median after-tax income",
            "row_count": len(income_df),
            "output_path": str(bronze_path),
        }
    )
    context.log.info(
        f"Materialized {len(income_df)} income rows to {bronze_path}"
    )

    return bronze_path
