select
    cast(reference_date as date) as reference_date,
    cast(cpi_value as double) as cpi_value,
    cast(series_id as varchar) as series_id,
    cast(source as varchar) as source
from read_parquet(
    'data/bronze/bank_of_canada/cpi/cpi.parquet'
)


