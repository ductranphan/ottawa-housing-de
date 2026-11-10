with rents as (

    select
        reference_year,
        geography,
        structure_type,
        unit_type,
        rent_value,
        lag(rent_value) over (
            partition by geography, structure_type, unit_type
            order by reference_year
        ) as previous_rent
    from {{ ref('stg_cmhc_rents') }}

),

cpi as (

    select
        reference_year,
        annual_average_cpi,
        lag(annual_average_cpi) over (
            order by reference_year
        ) as previous_cpi
    from {{ ref('int_annual_cpi') }}

)

select
    rents.reference_year,
    rents.geography,
    rents.structure_type,
    rents.unit_type,
    rents.rent_value,
    cpi.annual_average_cpi,

    case
        when rents.previous_rent is not null
        then 100.0
            * (rents.rent_value - rents.previous_rent)
            / rents.previous_rent
    end as rent_growth_percent,

    case
        when cpi.previous_cpi is not null
        then 100.0
            * (cpi.annual_average_cpi - cpi.previous_cpi)
            / cpi.previous_cpi
    end as cpi_growth_percent,

    rents.rent_value
        / nullif(cpi.annual_average_cpi, 0)
        * 100 as rent_in_2002_cpi_dollars

from rents
inner join cpi
    on rents.reference_year = cpi.reference_year