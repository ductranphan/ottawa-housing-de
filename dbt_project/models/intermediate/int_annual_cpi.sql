select
    extract(year from reference_date)::integer as reference_year,
    avg(cpi_value) as annual_average_cpi
from {{ ref('stg_cpi') }}
group by
    extract(year from reference_date)::integer
order by
    reference_year