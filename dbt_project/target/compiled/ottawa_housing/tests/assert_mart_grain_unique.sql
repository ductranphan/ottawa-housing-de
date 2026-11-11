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