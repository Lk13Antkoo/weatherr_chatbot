
# Chatbot AI application for local web

This responsity is for assignments including Programming with Python and Project AI use case

Author: HOANG AN PHAM

Matriculation number: 10245923

This application is weather chatbot AI running local web on Linux system. Overall, this application show how to integrate a local Large Language Model into a Chatbot and how to integrate them into a local web-based interface.

Requirements:

- linux operation
- 8GB ram minimum
- 8GB rom for downloading package and LLM model

## Set up
1. Clone respon
```bash
git clone https://github.com/Lk13Antkoo/weatherr_chatbot.git
cd weatherr_chatbot
```
2. Download fine-tuned quantized model
```bash
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
```

3. Create python virtual environment and activate it
```bash
python -m venv venv
source ./venv/bin/activate
```

4. Install packages
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Running
```bash
python run.py
```
Click on the localhost address (in the image) to open local web interface
![alt text](image.png)
Local web 
![alt text](image-1.png)
From terminal you can see the process, for debugging purpose only, the extracted place and weather information will be shown only on terminal.

