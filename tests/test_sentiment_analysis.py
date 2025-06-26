import time

from tqdm import tqdm  # Import tqdm
from transformers.models.bert import BertForSequenceClassification, BertTokenizer
from transformers.pipelines import pipeline

from nifty_analyzer.core import database as db


def main():
    conn = db.DatabaseManager()
    articles_df = conn.get_articles(has_sentiment=False, n=1000)

    headlines = articles_df['headline'].to_list()

    finbert_1 = BertForSequenceClassification.from_pretrained(
        'yiyanghkust/finbert-tone',
        num_labels=3,
        use_safetensors=True,  # Use safe tensors
    )

    tokenizer_1 = BertTokenizer.from_pretrained('yiyanghkust/finbert-tone')

    # set top_k=1 to get the most likely label or top_k=None to get all labels
    # device=-1 means CPU
    nlp_1 = pipeline(
        'sentiment-analysis',
        model=finbert_1,
        tokenizer=tokenizer_1,
        device=-1,
        top_k=1,
        framework='pt',
    )

    # nlp_1_res = nlp_1(headlines, batch_size=512) # Remove or comment out the original single run

    batch_sizes = [None, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]

    results = {}

    print(f'Testing inference time for {len(headlines)} headlines on CPU...')

    for batch_size in batch_sizes:
        start_time = time.time()
        # Run inference with tqdm
        # Note: tqdm might not show granular progress if the pipeline processes internally in large chunks
        # but it will show progress over the batches if the loop itself takes time.
        # For more granular progress, one might need to iterate and process headlines individually or in smaller manual batches.
        list(
            tqdm(
                nlp_1(headlines, batch_size=batch_size),
                total=len(headlines),
                desc=f'Batch Size {batch_size}',
            )
        )
        end_time = time.time()
        duration = end_time - start_time
        results[batch_size] = duration
        print(f'Batch Size: {batch_size}, Time Taken: {duration:.4f} seconds')

    print('\nInference Time Results:')
    for bs, t in results.items():
        print(f'Batch Size: {bs}, Time: {t:.4f} seconds')


if __name__ == '__main__':
    main()
