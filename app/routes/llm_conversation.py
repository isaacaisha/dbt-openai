from flask import Blueprint, render_template, flash
from flask_login import current_user
from datetime import datetime

from app.models.memory import Memory

llm_conversation_bp = Blueprint('llm_conversation', __name__, template_folder='templates')


@llm_conversation_bp.route("/get-all-conversations")
def get_all_conversations():
    try:
        owner_id = current_user.id

        # Fetch memories from the database
        conversations = Memory.query.filter_by(owner_id=owner_id).all()

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
                               current_user=current_user, owner_id=owner_id, conversations=serialized_conversations,
                               serialized_conversations=serialized_conversations,
                               date=datetime.now().strftime("%a %d %B %Y")
                               )

    except Exception as err:
        flash(f'Unexpected: {str(err)}, \ntype: {type(err)} 😭 ¡!¡')
        return render_template('authentication-error.html', error_message='User not authenticated',
                               current_user=current_user, date=datetime.now().strftime("%a %d %B %Y"))


@llm_conversation_bp.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    # Fetch memories from the database
    conversations = Memory.query.all()
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

    return render_template('database-conversations.html', date=datetime.now().strftime("%a %d %B %Y"),
                           current_user=current_user, serialized_conversations=serialized_conversations)
