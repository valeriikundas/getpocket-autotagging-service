import requests
import json
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Pocket consumer key from .env file
POCKET_CONSUMER_KEY = os.getenv('POCKET_CONSUMER_KEY')

# Predefined tags
TAGS = ['coding', 'curious', 'life', 'advice', 'investing', 'health']

# OLLaMa API endpoint and model selection
OLLAMA_API_ENDPOINT = 'http://localhost:11434/api/generate'
OLLAMA_MODEL = 'mistral:instruct'  # Updated model name as per instructions

# Limit the number of articles for autotagging
ARTICLES_LIMIT = 10

def get_access_token(consumer_key):
    # Step 1: Obtain a request token
    request_token_url = 'https://getpocket.com/v3/oauth/request'
    redirect_uri = 'https://example.com'  # Redirect URI after user authorization
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'X-Accept': 'application/json'}
    payload = {'consumer_key': consumer_key, 'redirect_uri': redirect_uri}
    response = requests.post(request_token_url, headers=headers, data=urlencode(payload))
    request_token = response.json().get('code')

    # Step 2: Redirect user to Pocket to authorize your application
    auth_url = f'https://getpocket.com/auth/authorize?request_token={request_token}&redirect_uri={redirect_uri}'
    print(f"Please visit this URL to authorize the application: {auth_url}")
    input("Press Enter after authorization...")

    # Step 3: Convert a request token into a Pocket access token
    access_token_url = 'https://getpocket.com/v3/oauth/authorize'
    payload = {'consumer_key': consumer_key, 'code': request_token}
    response = requests.post(access_token_url, headers=headers, data=urlencode(payload))
    if response.status_code == 200:
        access_token = response.json().get('access_token')
    else:
        print(f"Error from API: {response.text}")
        access_token = None
    return access_token


ACCESS_TOKEN = get_access_token(POCKET_CONSUMER_KEY)

def fetch_articles():
    headers = {
        'Content-Type': 'application/json',
        'X-Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'  # Added authorization header
    }
    payload = {
        'consumer_key': POCKET_CONSUMER_KEY,
        'access_token': ACCESS_TOKEN,
        'detailType': 'complete',
        'state': 'all'
    }
    response = requests.post('https://getpocket.com/v3/get', headers=headers, json=payload)
    if response.status_code == 200:
        articles = list(response.json()['list'].values())
        return articles[:ARTICLES_LIMIT]  # Limit the number of articles processed
    else:
        print(f"Failed to fetch articles: {response.text}")
        return []

def autotag_article(article_content):
    prompt = f"Given the article content: '{article_content}', which tag from the following list best fits the article? {', '.join(TAGS)}"
    data = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': True  # Adjusted for streaming response
    }
    print("Calling OLLaMa for autotagging...")
    response = requests.post(OLLAMA_API_ENDPOINT, json=data)
    if response.status_code == 200:
        # Handling streaming response
        final_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = json.loads(line.decode('utf-8'))
                if decoded_line.get('done', False):
                    final_response = decoded_line.get('response', '')
                    break
        # Assuming the response is a single tag from the predefined list
        tag = final_response.strip()
        print(f"Final response from OLLaMa: {final_response}")  # Log final response from OLLaMa
        return [tag] if tag in TAGS else []
    else:
        print(f"Failed to autotag article: {response.text}")
        return []

def update_article_tags(item_id, tags):
    headers = {
        'Content-Type': 'application/json',
        'X-Accept': 'application/json',
        'Authorization': f'Bearer {ACCESS_TOKEN}'  # Added authorization header
    }
    payload = {
        'consumer_key': POCKET_CONSUMER_KEY,
        'access_token': ACCESS_TOKEN,
        'actions': [
            {
                'action': 'tags_add',
                'item_id': item_id,
                'tags': ','.join(tags)
            }
        ]
    }
    response = requests.post('https://getpocket.com/v3/send', headers=headers, json=payload)










