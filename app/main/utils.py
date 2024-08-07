import base64
import requests
import json
from cryptography.fernet import Fernet
from flask import current_app
from app.models import Setting

def ensure_fernet_key(secret_key):
    if len(secret_key) < 32:
        secret_key += '=' * (32 - len(secret_key))
    secret_key_bytes = base64.urlsafe_b64encode(secret_key.encode())
    return Fernet(secret_key_bytes)

def encrypt_key(key):
    cipher_suite = ensure_fernet_key(current_app.config['SECRET_KEY'])
    return cipher_suite.encrypt(key.encode()).decode()

def decrypt_key(encrypted_key):
    cipher_suite = ensure_fernet_key(current_app.config['SECRET_KEY'])
    return cipher_suite.decrypt(encrypted_key.encode()).decode()

def get_api_key():
    settings = Setting.query.first()
    if settings and settings.gpt_api_key_hash:
        try:
            api_key = decrypt_key(settings.gpt_api_key_hash)
            if api_key:
                return api_key
        except Exception as e:
            current_app.logger.error(f"Error decrypting API key: {str(e)}")
            return None
    return None

def generate_text(prompt, api_key):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'model': 'gpt-4o-mini',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 150,
        'n': 1,
        'stop': None,
        'temperature': 0.7
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, data=json.dumps(data))
    response.raise_for_status()
    completion_response = response.json()
    return completion_response['choices'][0]['message']['content'].strip()

def generate_ingredients(product_name, api_key):
    prompt = f"Generate a list of natural ingredients for the product named {product_name}. Enclose any stabilizers or chemicals in brackets. Separate ingredients with commas. Only give ingredients, no other texts.Make the ingredients minimal and only include ingredients that got hight chances of inclusion. Also, no need to include any optional info."
    return generate_text(prompt, api_key)

def generate_nutritional_facts(ingredients, api_key):
    prompt = (
        f"Given the ingredients: {ingredients}, generate nutritional facts for a serving size of 100g in the following format: strictly follow the format, no other texts:\n"
        "Energy Value:    kcal\n"
        "Protein:         g\n"
        "Carbohydrates:   g\n"
        "Sugars:          g\n"
        "Total Fat:       g\n"
        "Saturated Fats:  g\n"
        "Trans Fats:      g\n"
        "Cholesterol:     mg\n"
        "Sodium:          mg"
    )
    return generate_text(prompt, api_key)

def generate_allergen_info(ingredients, api_key):
    prompt = f"Given the ingredients: {ingredients}, generate only allergen information in one sentence. Only give the allergen substance info, no other texts or from which ingredient, also no need to include optional info"
    return generate_text(prompt, api_key)
