select article_key, published_date_key, source_key, topic_key,
 1::integer as article_count, word_count, paragraph_count,
 loaded_at, updated_at, source_object_key
from {{ ref('stg_enriched_articles') }}
