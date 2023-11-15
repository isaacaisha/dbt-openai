import csv
import os
import openai
from dotenv import load_dotenv, find_dotenv
import secrets
from flask import Flask, render_template, request, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
from datetime import datetime
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from langchain.document_loaders import CSVLoader
from langchain.embeddings import OpenAIEmbeddings
import warnings
from pydantic import BaseModel
from typing import Optional
import psycopg2
import pytz
import json

warnings.filterwarnings('ignore')

app = Flask(__name__)
_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
# Generate a random secret key
secret_key = secrets.token_hex(199)

# Set it as the Flask application's secret key
app.secret_key = secret_key

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)

file = 'llm_memory.csv'
loader = CSVLoader(file_path=file)

docs = loader.load()
# Create a list of dictionaries with 'text' and 'metadata' fields
formatted_docs = [
    {
        'text': f"{doc.name if hasattr(doc, 'name') else 'Unnamed'}\n{doc.description if hasattr(doc, 'description') else 'No description'}",
        'metadata': {
            'source': 'llm_memory.csv',
            'row': i,
            'id': doc.id if hasattr(doc, 'id') else f'ID_{i}'
            # Replace 'id' with the actual attribute name or use a default
        }
    }
    for i, doc in enumerate(docs)
]

# Assuming that 'page_content' is the attribute used for embedding
texts_for_embedding = [getattr(doc, 'page_content', '') for doc in docs]
# print(f'texts_for_embedding:\n:{texts_for_embedding}\n')


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


class Memory(BaseModel):
    user_message: str
    llm_response: str
    memories: str
    conversations_summary: str
    published: bool = True
    rating: Optional[int] = None
    created_at: str


# Heroku provides the DATABASE_URL environment variable
DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(host=os.environ['host'], port=5432, database=os.environ['database'],
                        user=os.environ['user'],
                        password=os.environ['password'])
cursor = conn.cursor()

# Create OMR table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS omr (
        id SERIAL PRIMARY KEY,
        user_message TEXT,
        llm_response TEXT,
        conversations_summary TEXT,
        created_at TIMESTAMP
    )
""")
# cursor.execute("""TRUNCATE TABLE omr;""")
conn.commit()


def memory_csv():
    # Retrieve the new data for LLM memory
    new_memory_data_query = """SELECT id, conversations_summary, created_at 
    FROM OMR ORDER BY created_at DESC LIMIT 1;"""
    cursor.execute(new_memory_data_query)
    new_memory_data_result = cursor.fetchone()

    # Check if there is data
    if new_memory_data_result:
        new_memory_data_id, new_memory_data_summary, new_memory_data_created_at = new_memory_data_result

        # Convert conversations_summary from JSON to Python dictionary
        json.loads(new_memory_data_summary)

        # Save the last entry to llm_memory.csv
        with open('llm_memory.csv', 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header if the file is empty
            if csvfile.tell() == 0:
                csv_writer.writerow(["id", "conversations_summary", "created_at"])

            # Write the last entry
            csv_writer.writerow([new_memory_data_id, new_memory_data_summary, new_memory_data_created_at])


@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']

        # Use the LLM to generate a response based on user input
        response = conversation.predict(input=user_input)

        answer = response['output'] if response else None

    memory_buffer = memory.buffer
    memory_load = memory.load_memory_variables({})
    summary_buffer = memory_summary.load_memory_variables({})

    return render_template('index.html', writing_text_form=writing_text_form, answer=answer,
                           memory_load=memory_load, memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']

    if user_message:
        # # Extend the conversation with the user's message
        # response = conversation.predict(input=user_message)

        qdocs = "".join([docs[i].page_content for i in range(len(docs))])
        print(f'qdocs:\n{qdocs}\n')
        response = llm.call_as_llm(f"{qdocs} Use the <conversations_summary> to implement your response.\
        Question: {user_message}")
    else:
        response = conversation.predict(input=user_message)

    # Check if the response is a string, and if so, use it as the assistant's reply
    if isinstance(response, str):
        assistant_reply = response
    else:
        # If it's not a string, access the assistant's reply as you previously did
        assistant_reply = response.choices[0].message['content']

    # Convert the text response to speech using gTTS
    tts = gTTS(assistant_reply)

    # Create a temporary audio file
    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)

    memory_summary.save_context({"input": f"{user_message}"}, {"output": f"{response}"})
    conversations_summary = memory_summary.load_memory_variables({})
    conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

    current_time = datetime.now(pytz.timezone('Europe/Paris'))
    # Insert the conversation data into the OMR table
    insert_query = """
    INSERT INTO OMR (user_message, llm_response, conversations_summary, created_at)
    VALUES (%s, %s, %s, %s)
    """
    cursor.execute(insert_query, (user_message, assistant_reply, conversations_summary_str, current_time))
    conn.commit()

    print(f'User Input: {user_message} 😎')
    print(f'LLM Response:\n{assistant_reply} 😝\n')

    # Retrieve the new datas for LLM memory
    memory_csv()

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
    })


@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return send_file(audio_file_path, as_attachment=True)


@app.route('/show-history')
def show_story():
    memory_load = memory.load_memory_variables({})
    memory_buffer = memory.buffer
    summary_conversation = memory_summary.load_memory_variables({})

    return render_template('show-history.html', memory_load=memory_load, memory_buffer=memory_buffer,
                           summary_conversation=summary_conversation, date=datetime.now().strftime("%a %d %B %Y"))


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
