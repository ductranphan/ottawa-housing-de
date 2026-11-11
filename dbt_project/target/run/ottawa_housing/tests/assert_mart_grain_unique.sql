
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  select 
    reference_year,
    geography,
    structure_type,
    unit_type,
    count(*) as row_count
from "ottawa_housing"."main"."mart_housing_affordability"
group by 
    reference_year, 
    geography,
    structure_type,
    unit_type
having count(*) > 1
  
  
      
    ) dbt_internal_test