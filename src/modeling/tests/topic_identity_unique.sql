select model_version, model_topic_id
from {{ ref('dim_topic') }}
group by 1, 2 having count(*) > 1
