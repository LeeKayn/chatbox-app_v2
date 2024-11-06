# Simple Chatbox AI using Flask

## Download and Install

1. Clone the repository:

2. Create a virtual environment and install dependencies:
    ```sh
    python -m venv venv
    source venv/bin/activate  
    pip install -r requirements.txt
    ```

3. Run the application:
    ```sh
    python app.py
    ```

## Modify the chat response function

Open the `app.py` file and locate the `get_Chat_response` function. Modify this function to return the response from your model. For example:

```python
def get_Chat_response(text):
    # Add logic to get the response from your model
    response = "This is the response from your model"
    return response
