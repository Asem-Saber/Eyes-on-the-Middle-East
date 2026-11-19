select distinct on (topic_key) topic_key, model_version, topic_id as model_topic_id,
 case when topic_id = -1 then 'غير مصنف' else topic_label end as topic_label,
 topic_summary, (topic_id = -1) as is_outlier
from {{ ref('stg_enriched_articles') }}
order by topic_key, updated_at desc, article_id
