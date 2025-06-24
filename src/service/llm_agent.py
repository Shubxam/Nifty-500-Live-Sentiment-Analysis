import time
from os import getenv

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

load_dotenv()

# TODO: If getting google.genai.errors.ServerError: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'The model is overloaded. Please try again later.', 'status': 'UNAVAILABLE'}}
# Inform user that the model is overloaded and his query will take longer to process.
# handle this error gracefully and retry after some time.

# TODO: test the utility of libraries such as langchain, langgraph, smol-agents etc.
# TODO: verify if you can use smol-agents for any of your tasks.


def user_query_optimizer_agent(query: str = ''):
    client = genai.Client(
        api_key=getenv('GEMINI_API_KEY'),
    )

    model = 'gemini-2.5-flash'
    contents = types.Content(
            role='user',
            parts=[
                types.Part.from_text(text=query or """defense sector stocks with strong financial performance over the last 5 years."""),
            ],
        )
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,
        ),
        response_mime_type='text/plain',
        system_instruction=[
            types.Part.from_text(
                text="""You are an integral part of the project where a user has an idea for an index/portfolio to be executed in Indian Equity Market.
User will provide you with his idea, your job is to clean up the query and clearly evaluate user needs and parameters provided for index generation and present them in a query. A web search will be run against the query you produce.
 Use financial terms which include but are not limited to quarterly results, annual reports, revenue growth, EPS etc.
You should only answer with result you're most confident about."""
            ),
        ],
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        print(chunk.text, end='')


def google_search_agent(query: str = ''):
    pass


def structured_output_agent(query: str = ''):
    pass


if __name__ == '__main__':
    query = input("Enter your query: ")
    try:
        user_query_optimizer_agent(query)
    except ServerError:
        print("Model is overloaded. Request will be retried.")
        time.sleep(5)
        user_query_optimizer_agent(query)

