
  
  create view "ottawa_housing"."main"."stg_cmhc_rents__dbt_tmp" as (
    select
    cast(reference_year as integer) as reference_year,
    cast(geography as varchar) as geography,
    cast(structure_type as varchar) as structure_type,
    cast(unit_type as varchar) as unit_type,
    cast(rent_value as double) as rent_value,
    cast(vector as varchar) as vector,
    cast(source as varchar) as source
from read_parquet(
    'data/bronze/cmhc/rental_market/rents.parquet'
)
  );
