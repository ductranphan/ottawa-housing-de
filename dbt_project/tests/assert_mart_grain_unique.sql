select 
    reference_year,
    geography,
    structure_type,
    unit_type,
    count(*) as row_count
from {{ ref('mart_housing_affordability')}}            
group by 
    reference_year, 11
    geography,
    structure_type,
    unit_type
having count(*) > 1