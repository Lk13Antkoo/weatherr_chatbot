
import os
import warnings
import requests
import spacy
from flask import Flask, request, jsonify, render_template_string
from langchain import LlamaCpp, PromptTemplate

# Suppress warnings
warnings.filterwarnings("ignore")

# Load environment
WEATHER_API_KEY = "8915501f16cc4247981133248251205"
BASE_URL = 'http://api.weatherapi.com/v1/current.json'

# Initialize spaCy model
nlp = spacy.load('en_core_web_sm')

# Initialize LLM
llm = LlamaCpp(
    model_path='./llama-2-7b-chat.Q4_K_M.gguf',
    temperature=0.5,
   # n_gpu_layers=-1,
   n_gpu_layers=0,
    max_tokens=512,
    n_ctx=2048,
    top_p=1,
    seed=42,
    verbose=False,
)

# Prepare prompt template
template = """Instruct: {prompt}\nOutput:"""
prompt_template = PromptTemplate(
    template=template,
    input_variables=["prompt"]
)
basic_chain = prompt_template | llm

# Flask app setup
app = Flask(__name__)

# HTML template with AJAX-based chat and shutdown handling
HTML_PAGE = """
<!doctype html>
<title>Weather Assistant</title>
<style>
  body { font-family: Arial, sans-serif; margin: 2em; }
  #chat-history { list-style: none; padding: 0; }
  #chat-history li { margin-bottom: 1em; }
  .question { color: #1a237e; }
  .answer { color: #004d40; }
</style>
<h1>Ask about the weather</h1>
<form id="chat-form">
  <input type="text" name="question" id="question-input" size="60" placeholder="e.g. Will it rain in Paris today?" required>
  <input type="submit" id="submit-button" value="Ask">
</form>
<ul id="chat-history"></ul>
<script>
  const form = document.getElementById('chat-form');
  const history = document.getElementById('chat-history');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const question = document.getElementById('question-input').value;
    if (!question) return;

    // Display user's question
    const qElem = document.createElement('li');
    qElem.innerHTML = `<div class='question'><strong>Q:</strong> ${question}</div>`;
    history.appendChild(qElem);

    // Fetch answer
    const res = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const data = await res.json();

    // Display answer
    const aElem = document.createElement('li');
    if (data.error) {
      aElem.innerHTML = `<div class='answer'><strong>Error:</strong> ${data.error}</div>`;
    } else {
      aElem.innerHTML = `<div class='answer'><strong>A:</strong> ${data.answer}</div>`;
    }
    history.appendChild(aElem);
    form.reset();

    // Handle shutdown
    if (data.shutdown) {
      document.getElementById('question-input').disabled = true;
      document.getElementById('submit-button').disabled = true;
    }
  });
</script>
"""

# Global state: data storage and counters
data_base = {}
number_of_question = 0
max_question = 5


def extract_locations(text: str) -> list:
    """
    This function is used for Extracting place module. The function uses spaCy NER to identify 
    locations in the input text.
    
    inut param text: Description
    type text: str
    return: Description
    rtype: list contains the location in text
    """
    doc = nlp(text)
    locations = []
    for ent in doc.ents:
        # Extract locations using dateparser
        if ent.label_ in ["GPE", "LOC"]:
            locations.append(ent.text)
    print("Extracted locations:", locations)
    return locations


def get_current_weather(location: str) -> dict:
    """
    This function is used for Weather API Invocation Module. It fetches current weather data for a given 
    location using the WeatherAPI.
    
    input param location: the location to get weather info
    type location: str
    return: weather data in dict format
    rtype: dict
    """
    params = {'key': WEATHER_API_KEY, 'q': location}
    resp = requests.get(BASE_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    data['location'] = location
    print("Fetched weather data:", data)
    return data


def invoke_model(database: dict, question: str) -> str:
    """
    This function is used for invoking LLM model. It constructs a prompt using the provided database
    and user's question then calls the LLM to get an answer.
    
    input param database:  weather data
    input type database: dict
    input param question: question from user
    inputtype question: str

    return: LLM's answer
    rtype: str
    """
    if len(database) == 0: 
        location = None

    else:
        location = data_base['location']
    prompt_text = (
        f"You are a helpful weather assistant. You have access to the following data source:\n"
        f"Meta data: {database}. \n"
        f"Location: {location}. \n"
        "Think step by step and follow my instruction:\n"
        f"Here is my question: {question}.\n"
        "- First, analyze the question thoroughly.\n"
        "- Second, if the question is about weather conditions, provide an accurate answer based on available data and the location.\n"
        "Please write your final answer."
    )
    return basic_chain.invoke({"prompt": prompt_text})

@app.route('/', methods=['GET'])
def index():
    """
    This function renders the main HTML page for the weather chatbot.
    """
    return render_template_string(HTML_PAGE)

@app.route('/ask', methods=['POST'])
def ask_weather():
    """
    This function handles the /ask endpoint for processing user questions about the weather.
    It extracts the question from the request, determines the location, fetches weather data if needed,
    invokes the LLM model to get an answer, and returns the answer as a JSON response
    """
    global data_base, number_of_question
    payload = request.get_json() or {}
    question = payload.get('question', '')

    # Shutdown application
    if 'exit' in question.lower():
        shutdown = request.environ.get('werkzeug.server.shutdown')
        if shutdown:
            shutdown()
        return jsonify({'answer': 'Server shutting down...', 'shutdown': True}), 200

    # Question limit
    if number_of_question >= max_question -1:
        data_base.clear()
        number_of_question = 0
        return jsonify({'error': f'Exceeded {max_question} questions. Start over.'}), 429

    # Determine location
    locs = extract_locations(question)
    if locs:
        location = locs[0].lower()
    elif data_base.get('location'):
        location = data_base['location']
    else:
        return jsonify({'error': 'No location found in question.'}), 400

    # Fetch or reuse data
    if not data_base or data_base.get('location') != location:
        try:
            data_base = get_current_weather(location)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Invoke and increment
    answer = invoke_model(data_base, question)
    number_of_question += 1
    return jsonify({'answer': answer})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

