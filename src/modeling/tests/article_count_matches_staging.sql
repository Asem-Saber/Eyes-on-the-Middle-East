select 1 as mismatch
where (select count(*) from {{ ref('fct_articles') }}) <>
      (select count(*) from {{ ref('stg_enriched_articles') }})
