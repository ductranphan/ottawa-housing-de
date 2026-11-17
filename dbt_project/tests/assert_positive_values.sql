select
    'cpi' as metric,
    reference_date as metric_date,
    cpi_value as metric_value
from {{ ref('stg_cpi') }}
where cpi_value <= 0

union all

select 
    'rent' as metric,
    make_date(reference_year, 1, 1) as metric_date,
    rent_value as metric_value
from {{ ref('stg_cmhc_rents') }}
where rent_value <= 0

union all

select 
    'income' as metric,
    make_date(reference_year, 1, 1) as metric_date,
    income_value as metric_value
from {{ ref('stg_income') }}
where income_value <= 0

