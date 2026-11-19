with articles as (
 select *, to_date(published_date_raw, 'DD/MM/YYYY') as published_date,
        lower(substring(link from '^https?://([^/:?#]+)')) as domain
 from {{ source('news_staging', 'enriched_articles') }}
), prepared as (
 select *, regexp_replace(domain, '^www\.', '') as source_domain,
        (select string_agg(value, E'\n' order by ordinal)
         from jsonb_array_elements_text(full_content) with ordinality as p(value, ordinal)) as body_text
 from articles
)
select *,
 {{ stable_key('article_id') }} as article_key,
 {{ stable_key('source_domain') }} as source_key,
 {{ stable_key("jsonb_build_array(model_version, topic_id)::text") }} as topic_key,
 to_char(published_date, 'YYYYMMDD')::integer as published_date_key,
 case when trim(coalesce(body_text, '')) = '' then 0
      else cardinality(regexp_split_to_array(trim(body_text), '\s+')) end as word_count,
 jsonb_array_length(full_content) as paragraph_count
from prepared
