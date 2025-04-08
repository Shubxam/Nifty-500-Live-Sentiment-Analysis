import logging
from typing import Dict, List, Optional
from time import sleep

import pandas as pd
from huggingface_hub.inference_api import InferenceApi
from tqdm import tqdm

from config import HF_MODEL_NAME, BATCH_SIZE, API_TIMEOUT, MAX_RETRIES


class SentimentAnalyzer:
    def __init__(self, api_token: str):
        self.model = InferenceApi(
            repo_id=HF_MODEL_NAME,
            token=api_token,
            timeout=API_TIMEOUT
        )

    def _process_batch(self, headlines: List[str], retry_count: int = 0) -> Optional[List[Dict]]:
        """Process a batch of headlines with retry logic"""
        try:
            results = self.model(headlines)
            return results
        except Exception as e:
            if retry_count < MAX_RETRIES:
                logging.warning(f"Attempt {retry_count + 1} failed, retrying in {2 ** retry_count} seconds...")
                sleep(2 ** retry_count)  # Exponential backoff
                return self._process_batch(headlines, retry_count + 1)
            logging.error(f"Failed to process batch after {MAX_RETRIES} attempts: {str(e)}")
            return None

    def analyze_headlines(self, headlines_df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze sentiment of headlines in batches

        Parameters:
        -----------
        headlines_df : pd.DataFrame
            DataFrame with 'id' and 'headline' columns

        Returns:
        --------
        pd.DataFrame
            DataFrame with sentiment scores
        """
        all_results = []

        for i in tqdm(range(0, len(headlines_df), BATCH_SIZE), desc="Processing batches"):
            batch = headlines_df.iloc[i:i+BATCH_SIZE]
            batch_results = self._process_batch(batch['headline'].tolist())

            if batch_results:
                for idx, result in zip(batch.index, batch_results):
                    score_dict = {
                        'id': batch.loc[idx, 'id'],
                        'negative': next((item['score'] for item in result if item['label'] == 'negative'), 0),
                        'positive': next((item['score'] for item in result if item['label'] == 'positive'), 0),
                        'neutral': next((item['score'] for item in result if item['label'] == 'neutral'), 0)
                    }
                    score_dict['compound'] = score_dict['positive'] - score_dict['negative']
                    all_results.append(score_dict)

        return pd.DataFrame(all_results) if all_results else pd.DataFrame()
