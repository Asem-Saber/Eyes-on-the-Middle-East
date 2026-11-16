with bounds as (
 select min(published_date) as first_date, max(published_date) as last_date
 from {{ ref('stg_enriched_articles') }}
), dates as (
 select generate_series(first_date::timestamp, last_date::timestamp, interval '1 day')::date as full_date
 from bounds
)
select to_char(full_date, 'YYYYMMDD')::integer as date_key, full_date,
 extract(year from full_date)::integer as year,
 extract(quarter from full_date)::integer as quarter,
 extract(month from full_date)::integer as month,
 trim(to_char(full_date, 'Month')) as month_name,
 extract(day from full_date)::integer as day,
 extract(isodow from full_date)::integer as day_of_week,
 extract(week from full_date)::integer as iso_week,
 extract(isoyear from full_date)::integer as iso_year
from dates
