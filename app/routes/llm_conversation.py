from flask import Blueprint, render_template, request
from flask_login import current_user
from typing import Optional
from datetime import datetime

from app.models.memory import Memory

llm_conversation_bp = Blueprint('llm_conversation', __name__, template_folder='templates')

def get_conversations(owner_id=None, limit=None, offset=None, search=None, order_by_desc=False):
    query = Memory.query
    if owner_id is not None:
        query = query.filter_by(owner_id=owner_id)
    if search is not None:
        query = query.filter(Memory.user_message.ilike(f"%{search}%"))
    if order_by_desc:
        query = query.order_by(Memory.id.desc())
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all()

def serialize_conversation(conversation):
    return {
        "id": conversation.id,
        "owner_id": conversation.owner_id,
        "user_name": conversation.user_name,
        "user_message": conversation.user_message,
        "llm_response": conversation.llm_response,
        "conversations_summary": conversation.conversations_summary,
        'created_at': conversation.created_at.strftime("%a %d %B %Y %H:%M:%S"),
    }

@llm_conversation_bp.route("/get-all-conversations")
def get_all_conversations():
    if not current_user.is_authenticated:
        error_message = 'User not authenticated, RELOAD or LOGIN -¡!¡-'
        return render_template('all-conversations.html', error_message=error_message,
                               current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))

    owner_id = current_user.id

    # Get the total number of conversations
    total_conversations = Memory.query.filter_by(owner_id=owner_id).count()
    # Set the default limit to the total number of conversations
    limit = request.args.get('limit', default=total_conversations, type=int)

    # Get the offset from the query parameter, default to 0 if not provided
    offset = request.args.get('offset', default=None, type=int)

    # Get the search from the query parameter, default to None if not provided
    search = request.args.get('search', default=None, type=str)

    conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search)
    serialized_conversations = [serialize_conversation(conversation) for conversation in conversations]

    return render_template('conversation-all.html',
                           current_user=current_user, owner_id=owner_id,
                           limit=limit, offset=offset, search=search,
                           conversations=serialized_conversations,
                           date=datetime.now().strftime("%a %d %B %Y"))

@llm_conversation_bp.route("/convers-head-tail")
def convers_head_tail():
    if not current_user.is_authenticated:
        error_message = 'User not authenticated, RELOAD or LOGIN -¡!¡-'
        return render_template('conversation-head-tail.html', error_message=error_message,
                               current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))

    owner_id = current_user.id
    
    # Get the limit from the query parameter, default to 3 if not provided
    limit = request.args.get('limit', default=3, type=int)
    # Get the offset from the query parameter, default to 0 if not provided
    offset = request.args.get('offset', default=None, type=int)
    # Get the search from the query parameter, default to None if not provided
    search = request.args.get('search', default=None, type=str)

    first_conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search)
    serialized_first_conversations = [serialize_conversation(conversation) for conversation in first_conversations]

    last_conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search, order_by_desc=True)
    serialized_last_conversations = [serialize_conversation(conversation) for conversation in last_conversations]

    return render_template('conversation-head-tail.html',
                           current_user=current_user, owner_id=owner_id,
                           limit=limit, offset=offset, search=search,
                           first_conversations=serialized_first_conversations,
                           last_conversations=serialized_last_conversations,
                           date=datetime.now().strftime("%a %d %B %Y"))

@llm_conversation_bp.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    conversations = get_conversations()
    serialized_conversations = [serialize_conversation(conversation) for conversation in conversations]

    return render_template('database-conversations.html', date=datetime.now().strftime("%a %d %B %Y"),
                           current_user=current_user, serialized_conversations=serialized_conversations)
