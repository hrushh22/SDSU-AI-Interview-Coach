"""
Configuration file for AI Interview Coach
"""
import os
import json

# Try to load deployment configuration
def load_deployment_config():
    try:
        with open('config/deployment-config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

deployment_config = load_deployment_config()

# API Configuration
API_ENDPOINT = os.getenv('API_ENDPOINT', deployment_config.get('apiEndpoint', 'https://mlwoyrblv3.execute-api.us-west-2.amazonaws.com/dev'))

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', deployment_config.get('region', 'us-west-2'))
AUDIO_BUCKET = deployment_config.get('audioBucket', '')
RESUME_BUCKET = deployment_config.get('resumeBucket', '')
SESSIONS_TABLE = deployment_config.get('sessionsTable', '')

# Application Configuration
ENVIRONMENT = deployment_config.get('environment', 'dev')

# Streamlit Configuration
STREAMLIT_CONFIG = {
    'page_title': 'AI Interview Coach',
    'page_icon': '🎤',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

print(f"🔧 Configuration loaded - API Endpoint: {API_ENDPOINT}")