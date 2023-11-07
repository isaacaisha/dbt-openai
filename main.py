import os
import openai
from dotenv import load_dotenv, find_dotenv
from fastapi.responses import HTMLResponse, FileResponse
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from pydantic import BaseModel
from datetime import datetime
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load environment variables
load_dotenv(find_dotenv())

# Set OpenAI API key
openai.api_key = os.environ['OPENAI_API_KEY']

# Initialize the conversation chain and other components
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)


# Define a Pydantic model for user input
class UserInput(BaseModel):
    user_message: str


class TextAreaForm(BaseModel):
    userInput: Optional[str] = None


# Define a FastAPI route to render the template with the form
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def get_home(request: Request, answer: str = None):
    writing_text_form = TextAreaForm()
    return templates.TemplateResponse("index.html", {
        "writing_text_form": writing_text_form,
        "request": request,
        "answer": answer,
        "date": datetime.now().strftime("%a %d %B %Y")
    })


@app.post("/")
async def home(request: Request, user_input: UserInput = Form(...)):
    user_input_text = user_input.user_message
    answer = None

    user_input = user_input_text

    response = conversation.predict(input=user_input)

    answer = response['output'] if response else None

    memory_load = memory.load_memory_variables({})
    memory_buffer = memory.buffer

    memory_summary.save_context({"input": f"Summarize the memory.buffer:"}, {"output": f"{memory_buffer}"})
    summary_buffer = memory_summary.load_memory_variables({})

    return templates.TemplateResponse("index.html", {
        "request": request,
        "answer": answer,
        "memory_load": memory_load,
        "memory_buffer": memory_buffer,
        "summary_buffer": summary_buffer,
        "date": datetime.now().strftime("%a %d %B %Y")
    })


@app.post("/answer")
def answer(user_message: str = Form(...)):
    response = conversation.predict(input=user_message)

    if isinstance(response, str):
        assistant_reply = response
    else:
        assistant_reply = response.choices[0].message['content']

    tts = gTTS(assistant_reply)

    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)

    return {
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
    }


@app.get('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return FileResponse(audio_file_path, media_type='audio/mpeg', headers={"Content-Disposition": "attachment"})


@app.get("/show-history", response_class=HTMLResponse)
async def show_history(request: Request):
    memory_load = memory.load_memory_variables({})
    memory_buffer = memory.buffer

    memory_summary.save_context({"input": f"Summarize the conversation:"}, {"output": f"{conversation}"})
    summary_conversation = memory_summary.load_memory_variables({})

    return templates.TemplateResponse("show-history.html", {
        "request": request,
        "memory_load": memory_load,
        "memory_buffer": memory_buffer,
        "conversation": conversation,
        "summary_conversation": summary_conversation,
        "date": datetime.now().strftime("%a %d %B %Y")
    })


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=int(os.environ.get('PORT', 8000)))
