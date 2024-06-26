from flask import Blueprint, flash, render_template, request, jsonify, redirect, url_for
from flask_login import current_user
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from app.app_forms import ThemeChatForm, ForumChatForm
from app.memory import Theme, Message, db
from langdetect import detect

conversation_chat_forum_bp = Blueprint('conversation_chat_forum', __name__)

llm = ChatOpenAI(temperature=0.0, model="gpt-4o")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)


@conversation_chat_forum_bp.route('/chat-forum', methods=['GET', 'POST'])
def theme_chat_forum():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    theme_chat_form = ThemeChatForm()
    all_themes = Theme.query.all()

    if theme_chat_form.validate_on_submit():
        # Get the theme name and remove extra spaces
        theme_name = theme_chat_form.theme_name.data
        theme_name = ' '.join(theme_name.strip().split())
        
        theme = Theme.query.filter_by(theme_name=theme_name).first()
        if not theme:
            theme = Theme(theme_name=theme_name)
            db.session.add(theme)
            db.session.commit()
        return redirect(url_for('conversation_chat_forum.chat_forum', theme_name=theme.theme_name))
    return render_template('conversation-theme-chat.html', current_user=current_user, theme_chat_form=theme_chat_form,
                           all_themes=all_themes, date=datetime.now().strftime("%a %d %B %Y"))


@conversation_chat_forum_bp.route('/chat-forum/<theme_name>/', methods=['GET', 'POST'])
def chat_forum(theme_name):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    forum_chat_form = ForumChatForm()
    theme = Theme.query.filter_by(theme_name=theme_name).first()
    
    if request.method == 'POST' and forum_chat_form.validate_on_submit():
        message_value = forum_chat_form.message.data
        username = current_user.name
        
        # Save user message
        new_message = Message(value=message_value, user=username, theme=theme_name, date=datetime.utcnow())
        db.session.add(new_message)
        db.session.commit()

        # Generate and save LLM response
        llm_response, detected_lang = generate_llm_response(message_value)
        # Save LLM response if it was generated
        if isinstance(llm_response, str):
            llm_message = Message(value=llm_response, user='·SìįSí·Dbt·', theme=theme_name, date=datetime.utcnow())
            db.session.add(llm_message)
            db.session.commit()

        # Return success without additional message
        return jsonify({"success": True})
    
    return render_template('conversation-chat-forum.html', forum_chat_form=forum_chat_form,
                           username=current_user.name, theme_name=theme_name, theme_details=theme,
                           date=datetime.now().strftime("%a %d %B %Y"))


def generate_llm_response(user_message):
    response = conversation.predict(
        input="You are participating in a chat forum. Respond appropriately to user queries." + user_message
        )
    detected_lang = detect(user_message)

    print(f"user_input: {user_message}")
    print(f"response: {response}\n")

    return response, detected_lang


@conversation_chat_forum_bp.route('/chat/answer', methods=['POST'])
def chat_answer():
    user_message = request.form['prompt']
    print(f'User Input:\n{user_message} 😎\n')

    # Detect the language of the user's message
    detected_lang = detect(user_message)

    # Extend the conversation with the user's message
    response = conversation.predict(input=user_message)

    # Check if the response is a string, and if so, use it as the assistant's reply
    if isinstance(response, str):
        assistant_reply = response
    else:
        # If it's not a string, access the assistant's reply as you previously did
        assistant_reply = response.choices[0].message['content']

    print(f'·SìįSí·Dbt· Response:\n{assistant_reply} 😝\n')

    # Return the response as JSON, including both text and detected language
    return jsonify({
        "answer_text": assistant_reply,
        "detected_lang": detected_lang,
    })


@conversation_chat_forum_bp.route('/getMessages/<theme_name>/', methods=['GET'])
def get_messages(theme_name):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    messages = Message.query.filter_by(theme=theme_name).order_by(Message.date.asc()).all()
    messages_list = [{"user": msg.user, "value": msg.value, "date": msg.date.strftime("%Y-%m-%d %H:%M:%S")} for msg in messages]
    return jsonify({"messages": messages_list})
