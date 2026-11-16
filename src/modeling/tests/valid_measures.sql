select * from {{ ref('fct_articles') }}
where article_count <> 1 or word_count < 0 or paragraph_count < 0
