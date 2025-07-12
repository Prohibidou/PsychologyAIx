import sqlite3
import pandas as pd
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from collections import Counter
import sys
import os

# --- CONFIGURATION of this script ---
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, "tweets.db")
TABLE_NAME = 'liked_tweets'
COLUMN_NAME = 'text'
MODEL_PATH = 'Marxx01/PoliBERTuito'
TOKENIZER_PATH = 'pysentimiento/robertuito-base-uncased'
BATCH_SIZE = 16
CONFIDENCE_THRESHOLD = 0.7

PARTY_LABELS = {
    0: 'Popular Party',
    1: 'PSOE',
    2: 'Citizens',
    3: 'Podemos',
    4: 'Vox'
}

IDEOLOGY_MAP = {
    'Popular Party': 'Center Right',
    'PSOE': 'Far Left',
    'Citizens': 'Far Left',
    'Podemos': 'Far Left',
    'Vox': 'Right'
}

def get_tweets_from_db(db_path, table_name, column_name, limit):
    conn = sqlite3.connect(db_path)
    query = f"SELECT {column_name} FROM {table_name} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df[column_name].dropna().tolist()

def run_analysis(config):
    try:
        yield f"Loading tweets from the database..."
        all_tweets = get_tweets_from_db(DB_PATH, TABLE_NAME, COLUMN_NAME, config.TWEET_LIMIT)
        if not all_tweets:
            yield "No tweets found in the database."
            return

        yield f"Filtering {len(all_tweets)} tweets for political content..."
        
        try:
            device = 0 if torch.cuda.is_available() else -1
            classifier = pipeline("zero-shot-classification", model=config.POLITICAL_CLASSIFIER_MODEL, device=device)
        except Exception as e:
            yield f"Error loading political classifier: {e}"
            return

        candidate_labels = ["political", "non-political"]
        political_tweets = []
        non_political_tweets = []

        try:
            results = classifier(all_tweets, candidate_labels=candidate_labels, batch_size=BATCH_SIZE)
            for i, result in enumerate(results):
                if result['labels'][0] == 'political':
                    political_tweets.append(all_tweets[i])
                else:
                    non_political_tweets.append(all_tweets[i])
        except Exception as e:
            yield f"Error during political classification: {e}"
            political_tweets, non_political_tweets = [], all_tweets

        yield f"Found {len(political_tweets)} political tweets."

        if not political_tweets:
            yield {
                'analysis_results': None,
                'non_political_tweets': non_political_tweets
            }
            return

        yield f"Analyzing ideology of {len(political_tweets)} tweets..."
        try:
            tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)
            model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
            ideology_classifier = pipeline('text-classification', model=model, tokenizer=tokenizer, device=device, return_all_scores=True)
        except Exception as e:
            yield f"Error loading ideology model: {e}"
            return

        results = ideology_classifier(political_tweets, batch_size=BATCH_SIZE, truncation=True)
        ideology_counts = Counter()
        classified_details = []

        for i, result_list in enumerate(results):
            best_prediction = max(result_list, key=lambda x: x['score'])
            score = best_prediction['score']
            label_index = int(best_prediction['label'].split('_')[-1])
            ideology = 'Undetermined'
            if score >= CONFIDENCE_THRESHOLD:
                party_name = PARTY_LABELS.get(label_index)
                if party_name:
                    ideology = IDEOLOGY_MAP.get(party_name, 'Undetermined')
            ideology_counts[ideology] += 1
            classified_details.append((political_tweets[i], ideology, score))

        analysis_results = {
            "counts": ideology_counts,
            "details": classified_details
        }

        yield "Analysis complete."
        yield {
            'analysis_results': analysis_results,
            'non_political_tweets': non_political_tweets
        }
    except Exception as e:
        yield f"An error occurred during the ideology analysis process: {e}"