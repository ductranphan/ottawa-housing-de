from dagster import Definitions

from .assets.cpi_assets import bank_of_canada_cpi_bronze


defs = Definitions(
    assets=[bank_of_canada_cpi_bronze],
)
