select
    cast(reference_year as integer) as reference_year,
    cast(geography as varchar) as geography,
    cast(income_concept as varchar) as income_concept,
    cast(statistic as varchar) as statistic,
    cast(income_value as double) as income_value,
    cast(unit as varchar) as unit,
    cast(vector as varchar) as vector,
    cast(source as varchar) as source
from read_parquet(
    'data/bronze/statcan/income/income.parquet'
)
