select distinct source_key,
 case when source_domain in ('ajnet.me', 'aljazeera.net') then 'Al Jazeera'
      else source_domain end as source_name,
 source_domain as domain
from {{ ref('stg_enriched_articles') }}
