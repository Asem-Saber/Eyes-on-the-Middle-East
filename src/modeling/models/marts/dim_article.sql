select article_key, article_id, link as url, headline, summary, full_content
from {{ ref('stg_enriched_articles') }}
