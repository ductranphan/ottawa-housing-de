from dagster import Definitions

from .assets.cpi_assets import bank_of_canada_cpi_bronze
from .assets.cmhc_assets import cmhc_rental_market_bronze
from .assets.income_assets import statcan_income_bronze


defs = Definitions(
    assets=[
        bank_of_canada_cpi_bronze,
        cmhc_rental_market_bronze,
        statcan_income_bronze,
    ],
)
