"""
topic_modeling.py
=================
Trains a BERTopic model on Al Jazeera Arabic articles, saves the model,
and optionally runs inference on new text.

Converted from: notebooks/topic-modeling.ipynb

Usage
-----
Train and save:
    python scripts/topic_modeling.py

Run inference only (loads saved model):
    python scripts/topic_modeling.py --inference-only

Show visualisations during training (requires a display):
    python scripts/topic_modeling.py --visualize

Inference on custom Arabic text:
    python scripts/topic_modeling.py --inference-only --text "your arabic text here"
"""

import argparse
from pathlib import Path

import pandas as pd
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance
from bertopic import BERTopic

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "news" / "aljazeera_articles.json"
MODEL_DIR = ROOT_DIR / "Aljazeera_topics_model"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
MIN_TOPIC_SIZE = 5
N_NEIGHBORS = 15
N_COMPONENTS = 5
MIN_CLUSTER_SIZE = 5
TOP_N_WORDS = 10


# Training
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_json(path)
    df = df.sample(frac=1, random_state=101)
    print(f"Loaded {len(df)} articles from {path}")
    return df


def build_models():
    """Instantiate all sub-models for BERTopic."""

    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    umap_model = UMAP(
        n_neighbors=N_NEIGHBORS,
        n_components=N_COMPONENTS,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=MIN_CLUSTER_SIZE,
        min_samples=3,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )

    vectorizer_model = CountVectorizer(
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
    )

    keybert_model = KeyBERTInspired()
    mmr_model = MaximalMarginalRelevance(diversity=0.3)
    representation_model = {
        "KeyBERT": keybert_model,
        "MMR": mmr_model,
    }

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        representation_model=representation_model,
        top_n_words=TOP_N_WORDS,
        min_topic_size=MIN_TOPIC_SIZE,
        nr_topics="auto",
        language="arabic",
        calculate_probabilities=True,
        verbose=True,
    )

    return topic_model, embedding_model


def train(visualize: bool = False):
    """Train BERTopic model, optionally show visualisations, and save."""

    df = load_data(DATA_PATH)
    documents = df["cleaned_docs"].tolist()

    topic_model, embedding_model = build_models()

    print("Encoding documents ...")
    embeddings = embedding_model.encode(documents, show_progress_bar=True)
    print(f"Embeddings shape: {embeddings.shape}")

    print("Fitting BERTopic ...")
    topics, probabilities = topic_model.fit_transform(documents, embeddings)
    n_topics = len(set(topics)) - (1 if -1 in topics else 0)
    print(f"Found {n_topics} topics")

    print(f"\nSample document (index 10):")
    print(f"  Article : {documents[10][:120]} ...")
    print(f"  Topic   : {topics[10]}")

    topic_info = topic_model.get_topic_info()
    print(f"\nTop topics:\n{topic_info.head()}")

    if visualize:
        _show_visualisations(topic_model, documents, embeddings)

    print(f"\nSaving model to: {MODEL_DIR}")
    topic_model.save(
        str(MODEL_DIR),
        serialization="safetensors",
        save_embedding_model=EMBEDDING_MODEL,
        save_ctfidf=True,
    )
    print("Model saved successfully.")

    return topic_model, topics, probabilities, embeddings, documents


def _show_visualisations(topic_model, documents, embeddings):
    """Generate BERTopic visualisations (requires a display or browser)."""

    umap_2d = UMAP(
        n_components=2,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    reduced_embeddings = umap_2d.fit_transform(embeddings)

    topic_model.visualize_documents(
        documents,
        reduced_embeddings=reduced_embeddings,
        width=1600,
        hide_annotations=True,
    ).show()

    topic_model.visualize_topics().show()
    topic_model.visualize_barchart().show()
    topic_model.visualize_heatmap(n_clusters=30).show()
    topic_model.visualize_hierarchy().show()


# Inference
def load_model(model_dir: Path = MODEL_DIR) -> BERTopic:
    """Load a previously saved BERTopic model."""
    print(f"Loading model from: {model_dir}")
    topic_model = BERTopic.load(str(model_dir))
    print("Model loaded.")
    return topic_model


def predict(topic_model: BERTopic, text: str) -> dict:
    """
    Run inference on a single Arabic text string.

    Returns a dict with keys: topic_id, confidence, label, keywords.
    """
    topic_pred, topic_prob = topic_model.transform([text])
    predicted_id = topic_pred[0]
    confidence = float(max(topic_prob[0]))

    topic_info = topic_model.get_topic_info(predicted_id)
    predicted_label = topic_info.values[0]
    keywords = topic_model.get_topic(predicted_id)

    result = {
        "topic_id": predicted_id,
        "confidence": confidence,
        "label": predicted_label,
        "keywords": keywords,
    }

    print(f"Predicted Topic ID : {predicted_id}")
    print(f"Predicted Label    : {predicted_label}")
    print(f"Confidence Score   : {confidence:.4f}")
    print(f"Top Keywords       : {keywords}")

    return result


DEMO_TEXT = (
    "يحرص الباحثون، الذين بدؤوا مهامهم في أوقات مبكرة من الحرب الإسرائيلية على القطاع، "
    "على جمع كل القرائن التي صاحبت الجرائم والمجازر التي استخدم فيها الاحتلال أسلحة محرمة دوليا، "
    "راح ضحيتها أكثر من 72 ألفا، وتركت آلاف الملفات العالقة ما بين مفقودين وأسرى ومدفونين تحت الركام"
)


# CLI entry-point

def parse_args():
    parser = argparse.ArgumentParser(
        description="Train or run inference with a BERTopic model on Al Jazeera articles."
    )
    parser.add_argument(
        "--inference-only",
        action="store_true",
        help="Skip training; load saved model and run inference on demo text.",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Show interactive BERTopic visualisations after training (requires a display).",
    )
    parser.add_argument(
        "--text",
        type=str,
        default=None,
        help="Custom Arabic text for inference (used with --inference-only).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.inference_only:
        topic_model = load_model()
        text = args.text or DEMO_TEXT
        predict(topic_model, text)
    else:
        train(visualize=args.visualize)
        topic_model = load_model()
        predict(topic_model, DEMO_TEXT)


if __name__ == "__main__":
    main()
