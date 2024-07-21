import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
import ssl
def extract_resources(text):
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    # Download required NLTK data #############    
    nltk.download('punkt')
    nltk.download('stopwords')
    sentences = sent_tokenize(text)
    resources = {}

    for sentence in sentences:
        words = word_tokenize(sentence)
        stop_words = set(stopwords.words('english'))
        filtered_words = [word.lower() for word in words if word.lower() not in stop_words]
        stemmer = PorterStemmer()
        stemmed_words = [stemmer.stem(word) for word in filtered_words]

        if 'ec2' in stemmed_words:
            resources['ec2'] = {}
            for word in stemmed_words:
                if word.startswith('t'):
                    resources['ec2']['instance_type'] = word
                elif word.startswith('ami'):
                    resources['ec2']['ami'] = word

        elif 's3' in stemmed_words:
            resources['s3'] = {}
            for word in stemmed_words:
                if word.endswith('bucket'):
                    resources['s3']['name'] = word
                elif word == 'privat':
                    resources['s3']['acl'] = 'private'
                elif word == 'public':
                    resources['s3']['acl'] = 'public-read'
    return resources
#################################################
import requests
def Generate_Terraform(message):
    # Replace with your API key
    api_key = ""

    # Replace with your ChatGPT model ID
    model_id = "gpt-4o"
    prompt = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": message
        }
        ]
    # Compose the API request
    data = {
        "messages": prompt,
        "model": model_id
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Send the request to the API
    response = requests.post(
        f"https://api.openai.com/v1/chat/completions",
        json=data,
        headers=headers
    )

    # Extract the generated message from the response
    completion = response.json()["choices"][0]['message']['content']
    return completion
######################################################
import re
def extract_code_blocks(text):
    # Regex to find code blocks
    code_block_pattern = re.compile(r'```hcl(.*?)```', re.DOTALL)
    # Find all matches
    code_blocks = code_block_pattern.findall(text)
    
    # Join all code blocks with double newline between them
    return "\n\n".join(code_blocks).strip()
import json
def create_terraform_message_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    resources = data.keys()
    message_parts = []

    for resource, specs in data.items():
        specs_list = [f"- {key}: {value}" for key, value in specs.items()]
        specs_str = "\n  ".join(specs_list)
        message_parts.append(f"{resource}:\n  {specs_str}")

    message = f"""
Create a Terraform configuration to deploy the following resources {list(data.keys())} with their specifications:
{chr(10).join(message_parts)}
    """
    return message