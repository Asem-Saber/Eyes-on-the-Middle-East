CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE TABLE IF NOT EXISTS staging.enriched_articles (
 article_id text PRIMARY KEY,
 link text NOT NULL,
 headline text NOT NULL,
 summary text NOT NULL,
 full_content jsonb NOT NULL CHECK (jsonb_typeof(full_content) = 'array'),
 published_date_raw text NOT NULL,
 topic_id integer NOT NULL,
 topic_label text,
 topic_summary text,
 model_version text NOT NULL,
 source_object_key text NOT NULL,
 load_batch_id uuid NOT NULL,
 payload_hash text NOT NULL,
 loaded_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now()
);
