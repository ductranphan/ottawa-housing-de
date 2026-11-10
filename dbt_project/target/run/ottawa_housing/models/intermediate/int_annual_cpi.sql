
  
  create view "ottawa_housing"."main"."int_annual_cpi__dbt_tmp" as (
    select
    extract(year from reference_date)::integer as reference_year,
    avg(cpi_value) as annual_average_cpi
from "ottawa_housing"."main"."stg_cpi"
group by
    extract(year from reference_date)::integer
order by
    reference_year
  );
