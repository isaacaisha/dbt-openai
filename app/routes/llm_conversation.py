from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from datetime import datetime

from app.memory import User, Memory, Theme, Message, MemoryTest, BlogPost, WebsiteReview, db
from app.app_forms import DatabaseForm


llm_conversation_bp = Blueprint('llm_conversation', __name__, template_folder='templates')


def get_conversations(owner_id=None, limit=None, offset=None, search=None, order_by_desc=False, liked_value=None):
    query = Memory.query
    if owner_id is not None:
        query = query.filter_by(owner_id=owner_id)
    if search is not None:
        query = query.filter(Memory.user_message.ilike(f"%{search.strip()}%"))
    if liked_value is not None:
        query = query.filter(Memory.liked == liked_value)
    if order_by_desc:
        query = query.order_by(Memory.id.desc())
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return query.all()


def serialize_conversation(conversation, last_summary_only=True):
    summary = conversation.conversations_summary.split('\n')[-1] if last_summary_only else conversation.conversations_summary
    return {
        "id": conversation.id,
        "owner_id": conversation.owner_id,
        "user_name": conversation.user_name,
        "user_message": conversation.user_message,
        "llm_response": conversation.llm_response,
        "conversations_summary": summary,
        "created_at": conversation.created_at.strftime("%a %d %B %Y %H:%M:%S"),
        "liked": conversation.liked,
    }


@llm_conversation_bp.route("/get-all-conversations")
def get_all_conversations():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    owner_id = current_user.id

    total_conversations = Memory.query.filter_by(owner_id=owner_id).count()
    limit = request.args.get('limit', default=total_conversations, type=int)
    offset = request.args.get('offset', default=None, type=int)
    search = request.args.get('search', default=None, type=str)

    conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search)
    serialized_conversations = [serialize_conversation(conversation) for conversation in conversations]

    # Check if any conversations were found for the search term
    if not serialized_conversations:
        search_message = f"No conversations found for search term: '{search}'"
        return render_template('conversation-all.html',
                               current_user=current_user, owner_id=owner_id,
                               limit=limit, offset=offset, search=search,
                               search_message=search_message,
                               date=datetime.now().strftime("%a %d %B %Y"))

    return render_template('conversation-all.html',
                           current_user=current_user, owner_id=owner_id,
                           limit=limit, offset=offset, search=search,
                           conversations=serialized_conversations,
                           date=datetime.now().strftime("%a %d %B %Y"))


@llm_conversation_bp.route("/convers-head-tail")
def convers_head_tail():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    owner_id = current_user.id

    limit = request.args.get('limit', default=3, type=int)
    offset = request.args.get('offset', default=None, type=int)
    search = request.args.get('search', default=None, type=str)

    first_conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search)
    serialized_first_conversations = [serialize_conversation(conversation) for conversation in first_conversations]

    last_conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search, order_by_desc=True)
    serialized_last_conversations = [serialize_conversation(conversation) for conversation in last_conversations]

    # Check if any conversations were found for the search term
    if not (serialized_first_conversations or serialized_last_conversations):
        search_message = f"No conversations found for search term: '{search}'"
        return render_template('conversation-head-tail.html',
                               current_user=current_user, owner_id=owner_id,
                               limit=limit, offset=offset, search=search,
                               search_message=search_message,
                               date=datetime.now().strftime("%a %d %B %Y"))

    return render_template('conversation-head-tail.html',
                           current_user=current_user, owner_id=owner_id,
                           limit=limit, offset=offset, search=search,
                           first_conversations=serialized_first_conversations,
                           last_conversations=serialized_last_conversations,
                           date=datetime.now().strftime("%a %d %B %Y"))


@llm_conversation_bp.route('/conversation-show-history')
def show_story():
    if current_user.is_authenticated:
        owner_id = current_user.id

        limit = request.args.get('limit', default=3, type=int)
        offset = request.args.get('offset', default=None, type=int)
        search = request.args.get('search', default=None, type=str)

        # Fetch conversations based on the provided search parameters
        memory_load = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search, order_by_desc=True)
        serialized_memory_load = [serialize_conversation(memory, last_summary_only=True) for memory in memory_load]

        if memory_load:
            memory_buffer = f'- {current_user.name}(owner_id:{owner_id}):\n\n'
            memory_buffer += '\n\n'.join(
                [f'- {memory.user_name}: {memory.user_message}\n\n·SìįSí·Dbt·: {memory.llm_response}\n\n- Created at: { memory.created_at.strftime('%Y-%m-%d %H:%M:%S') }\n\n' + '-' * 19 for memory in memory_load]
            )

            summary_conversations = '\n\n'.join([memory.conversations_summary.split('\n')[-1] for memory in memory_load])

            return render_template('conversation-show-history.html',
                                   current_user=current_user, owner_id=owner_id,
                                   memory_load=memory_load, memory_buffer=memory_buffer,
                                   summary_conversations=summary_conversations,
                                   serialized_memory_load=serialized_memory_load,
                                   limit=limit, offset=offset, search=search,
                                   date=datetime.now().strftime("%a %d %B %Y"))
        else:
            search_message = f"No conversations found for search term: '{search}'"
            return render_template('conversation-show-history.html', current_user=current_user, owner_id=owner_id,
                                   memory_load=memory_load, memory_buffer='',
                                   summary_conversations='',
                                   serialized_memory_load=serialized_memory_load,
                                   limit=limit, offset=offset, search=search,
                                   search_message=search_message,
                                   date=datetime.now().strftime("%a %d %B %Y"))
    else:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))


@llm_conversation_bp.route('/update-like/<int:conversation_id>', methods=['POST'])
def update_like(conversation_id):
    # Get the liked status from the request data
    liked = request.json.get('liked')

    # Find the corresponding Memory object in the database using db.session.get()
    conversation = db.session.get(Memory, conversation_id)

    # Update the liked status of the conversation
    conversation.liked = liked

    # Add the updated conversation object to the session
    db.session.add(conversation)

    # Commit the changes to the database
    db.session.commit()

    # Return a success response
    return 'Liked status updated successfully', 200


@llm_conversation_bp.route('/liked-conversations')
def liked_conversations():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    owner_id = current_user.id

    limit = request.args.get('limit', default=3, type=int)
    offset = request.args.get('offset', default=None, type=int)
    search = request.args.get('search', default=None, type=str)

    liked_conversations = get_conversations(owner_id=owner_id, limit=limit, offset=offset, search=search, order_by_desc=True, liked_value=1)

    serialized_liked_conversations = [serialize_conversation(conversation, last_summary_only=True) for conversation in liked_conversations]

    if not serialized_liked_conversations:
        search_message = f"No conversations found for search term: '{search}'"
        return render_template('conversation-liked.html',
                               current_user=current_user, owner_id=owner_id,
                               limit=limit, offset=offset, search=search,
                               search_message=search_message,
                               date=datetime.now().strftime("%a %d %B %Y"))
    
    return render_template('conversation-liked.html',
                           current_user=current_user,
                           owner_id=owner_id,
                           liked_conversations=serialized_liked_conversations,
                           limit=limit, offset=offset, search=search,
                           date=datetime.now().strftime("%a %d %B %Y"))


@llm_conversation_bp.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    conversations = get_conversations()
    serialized_conversations = [serialize_conversation(conversation) for conversation in conversations]

    all_users = User.query.all()
    all_themes = Theme.query.all()
    all_messages = Message.query.all()

    database_form = DatabaseForm()

    # Fetch MemoryTest data
    memory_tests = MemoryTest.query.all()

    # Fetch BlogPost data
    all_blog_potos = BlogPost.query.all()

    # Fetch PortfolioReview data
    all_website_reviews = WebsiteReview.query.all()
    
    # Serialize MemoryTest data
    serialized_memory_tests = [{
        'id': memory.id,
        'user_message': memory.user_message,
        'llm_response': memory.llm_response,
        'conversations_summary': memory.conversations_summary,
        'created_at': memory.created_at.strftime("%Y-%m-%d %H:%M:%S")
    } for memory in memory_tests]

    return render_template('database-conversations.html', date=datetime.now().strftime("%a %d %B %Y"),
                           current_user=current_user, serialized_conversations=serialized_conversations,
                           users=all_users, themes=all_themes, messages=all_messages, database_form=database_form,
                           serialized_memory_tests=serialized_memory_tests, all_blog_potos=all_blog_potos,
                           all_website_reviews=all_website_reviews)
