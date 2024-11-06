from flask import Flask, render_template, request, jsonify
import threading
import requests
import torch
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/get', methods=['GET', 'POST'])
def chat():
    msg = request.form["msg"]
    input = msg
    return get_Chat_response(input)

import requests

def get_Chat_response(text):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    api_key = "AIzaSyA2PTzQlE2VS_8RAbkuO4Af5ENd0oI4Hm4"  # Replace with your actual API key
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "contents": [
            {
                "parts": [
                    {"text": text}
                ]
            }
        ]
    }

    params = {
        "key": api_key
    }

    try:
        response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        response.raise_for_status()
        response_json = response.json()

        # Extracting the response from 'candidates'
        if 'candidates' in response_json and response_json['candidates']:
            return response_json['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Unexpected response format or missing content."

    except requests.exceptions.Timeout:
        return "Request timed out. Please try again later."
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"
@app.route('/upload_file', methods=['POST'])
def upload_file():
    file_content = request.form['file_content']
    # Process the file content as needed
    response = "Received file content: " + file_content  # Modify this as needed
    return jsonify(response)
if __name__ == '__main__':
    app.run()