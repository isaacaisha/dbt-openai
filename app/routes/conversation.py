from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.chains import ConversationChain

from app.databases.database import get_db
from app.models.memory import Memory, db

from app.forms.app_forms import TextAreaForm

conversation_bp = Blueprint('conversation', __name__)

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)


# Fetch memories from the database
with get_db() as db:
    # memories = db.query(Memory).all()
    test = db.query(Memory).all()


@conversation_bp.route("/", methods=["GET", "POST"])
def home():
    form = TextAreaForm()
    response = None
    user_input = None

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}\n")

            user_input = request.form['writing_text']
            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        print(f"user_input: {user_input}")
        print(f"response: {response}\n")

        return render_template('index.html', form=form,
                               current_user=current_user, response=response, memory_buffer=memory_buffer,
                               memory_load=memory_load, date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('home'))


@conversation_bp.route("/conversation-answer", methods=["GET", "POST"])
def conversation_answer():
    form = TextAreaForm()
    answer = None
    owner_id = None

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}")

            user_input = request.form['writing_text']
            owner_id = current_user.id

            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)
            answer = response['output'] if response else None

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({'owner_id': owner_id})
        summary_buffer = memory_summary.load_memory_variables({'owner_id': owner_id})

        return render_template('conversation-answer.html', current_user=current_user,
                               form=form, answer=answer, memory_load=memory_load,
                               memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('conversation_answer'))


@conversation_bp.route('/show-history')
def show_story():
    try:
        owner_id = current_user.id

        # Modify the query to filter records based on the current user's ID
        summary_conversation = memory_summary.load_memory_variables({'owner_id': owner_id})
        memory_load = memory.load_memory_variables({'owner_id': owner_id})
        memory_buffer = f'{current_user.name}:\n{memory.buffer_as_str}'

        print(f'memory_buffer_story:\n{memory_buffer}\n')
        print(f'memory_load_story:\n{memory_load}\n')
        print(f'summary_conversation_story:\n{summary_conversation}\n')

        return render_template('show-history.html', current_user=current_user, memory_load=memory_load,
                               memory_buffer=memory_buffer, summary_conversation=summary_conversation,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('authentication_error'))


@conversation_bp.route("/get-all-conversations")
def get_all_conversations():
    try:
        owner_id = current_user.id
        conversations = db.query(Memory).filter_by(owner_id=owner_id).all()
        # Create a list to store serialized data for each Memory object
        serialized_conversations = []

        for conversation_ in conversations:
            serialized_history = {
                "id": conversation_.id,
                "owner_id": conversation_.owner_id,
                "user_name": conversation_.user_name,
                "user_message": conversation_.user_message,
                "llm_response": conversation_.llm_response,
                "conversations_summary": conversation_.conversations_summary,
                'created_at': conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S"),
            }

            serialized_conversations.append(serialized_history)

        return render_template('all-conversations.html',
                               current_user=current_user,
                               conversations=serialized_conversations,
                               serialized_conversations=serialized_conversations,
                               date=datetime.now().strftime("%a %d %B %Y")
                               )

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('authentication_error'))


@conversation_bp.route('/conversation/<int:conversation_id>')
def get_conversation(conversation_id):
    conversation_ = db.query(Memory).filter_by(id=conversation_id).first()

    try:
        if not conversation_:
            # Conversation not found, return a not found message
            return redirect(url_for('conversation_not_found', conversation_id=conversation_id))

        if conversation_.owner_id != current_user.id:
            # User doesn't have access, return a forbidden message
            return redirect(url_for('conversation_forbidden', conversation_id=conversation_id))

        else:
            # Format created_at timestamp
            formatted_created_at = conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S")
            return render_template('conversation-details.html', current_user=current_user,
                                   conversation_=conversation_, formatted_created_at=formatted_created_at,
                                   conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@conversation_bp.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    # Retrieve all conversations from the database
    conversations = test
    # Convert the conversations to a list of dictionaries
    serialized_conversations = []

    for conversation_ in conversations:
        conversation_dict = {
            'id': conversation_.id,
            'user_name': conversation_.user_name,
            'user_message': conversation_.user_message,
            'llm_response': conversation_.llm_response,
            'created_at': conversation_.created_at.strftime("%a %d %B %Y"),
        }

        serialized_conversations.append(conversation_dict)

    return render_template('database-conversations.html',
                           current_user=current_user,
                           serialized_conversations=serialized_conversations,
                           date=datetime.now().strftime("%a %d %B %Y")
                           )
