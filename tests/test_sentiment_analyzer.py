import pytest
import pandas as pd
from unittest.mock import MagicMock, patch

from services.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def mock_huggingface_api():
    with patch('huggingface_hub.inference_api.InferenceApi') as mock:
        yield mock


@pytest.fixture
def analyzer(mock_huggingface_api):
    return SentimentAnalyzer("dummy_token")


def test_process_batch_success(analyzer, mock_huggingface_api):
    mock_response = [
        [
            {"label": "positive", "score": 0.9},
            {"label": "neutral", "score": 0.05},
            {"label": "negative", "score": 0.05}
        ]
    ]
    mock_huggingface_api.return_value.__call__.return_value = mock_response
    
    result = analyzer._process_batch(["Test headline"])
    assert result == mock_response


def test_process_batch_retry(analyzer, mock_huggingface_api):
    mock_huggingface_api.return_value.__call__.side_effect = [
        Exception("API Error"),
        [
            [
                {"label": "positive", "score": 0.9},
                {"label": "neutral", "score": 0.05},
                {"label": "negative", "score": 0.05}
            ]
        ]
    ]
    
    result = analyzer._process_batch(["Test headline"])
    assert mock_huggingface_api.return_value.__call__.call_count == 2
    assert result is not None


def test_analyze_headlines(analyzer, mock_huggingface_api):
    mock_response = [
        [
            {"label": "positive", "score": 0.9},
            {"label": "neutral", "score": 0.05},
            {"label": "negative", "score": 0.05}
        ]
    ]
    mock_huggingface_api.return_value.__call__.return_value = mock_response
    
    test_df = pd.DataFrame({
        'id': [1],
        'headline': ['Test headline']
    })
    
    result_df = analyzer.analyze_headlines(test_df)
    
    assert not result_df.empty
    assert 'compound' in result_df.columns
    assert result_df.iloc[0]['positive'] == 0.9
    assert result_df.iloc[0]['compound'] == 0.85  # 0.9 - 0.05