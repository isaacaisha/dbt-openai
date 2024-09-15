# LLM_CONVERSATION.PY

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from dataclasses import dataclass
from datetime import datetime

from app.memory import User, Memory, Theme, Message, MemoryTest, BlogPost, WebsiteReview, DrawingDatabase, db
from app.app_forms import DatabaseForm


llm_conversation_bp = Blueprint('llm_conversation', __name__, template_folder='templates')


@dataclass
class ConversationFilters:
    owner_id: int
    limit: int = None
    offset: int = 0
    search: str = None
    order_by_desc: bool = False
    liked_value: int = None
    

def get_conversations(filters: ConversationFilters):
    query = Memory.query.filter_by(owner_id=filters.owner_id)
    if filters.liked_value is not None:
        query = query.filter_by(liked=filters.liked_value)
    if filters.search:
        search_term = f"%{filters.search.strip()}%"
        query = query.filter(Memory.user_message.ilike(search_term))
    if filters.order_by_desc:
        query = query.order_by(Memory.id.desc())
    if filters.limit:
        query = query.limit(filters.limit)
    if filters.offset:
        query = query.offset(filters.offset)
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


def render_conversation_template(template_name, filters, serialized_conversations, **extra_context):
    context = {
        "current_user": current_user,
        "limit": filters.limit,
        "offset": filters.offset,
        "search": filters.search,
        "conversations": serialized_conversations,
        "date": datetime.now().strftime("%a %d %B %Y")
    }
    context.update(extra_context)
    
    return render_template(template_name, **context)


@llm_conversation_bp.route("/get-all-conversations")
def get_all_conversations():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    filters = ConversationFilters(
        owner_id=current_user.id,
        limit=request.args.get('limit', default=None, type=int),
        offset=request.args.get('offset', default=0, type=int),
        search=request.args.get('search', default=None, type=str),
        order_by_desc=True
    )

    conversations = get_conversations(filters)
    serialized_conversations = [serialize_conversation(conversation) for conversation in conversations]

    if not serialized_conversations:
        return render_conversation_template('conversation-all.html', filters, serialized_conversations,
                                            search_message=f"No conversations found for search term: '{filters.search}'")

    return render_conversation_template('conversation-all.html', filters, serialized_conversations)


@llm_conversation_bp.route('/liked-conversations')
def liked_conversations():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    filters = ConversationFilters(
        owner_id=current_user.id,
        limit=request.args.get('limit', default=None, type=int),
        offset=request.args.get('offset', default=0, type=int),
        search=request.args.get('search', default=None, type=str),
        order_by_desc=True,
        liked_value=1
    )

    liked_conversations = get_conversations(filters)
    serialized_liked_conversations = [serialize_conversation(conversation) for conversation in liked_conversations]
    liked_conversations_count = len(liked_conversations)  # Adding this back

    if not serialized_liked_conversations:
        return render_conversation_template('conversation-liked.html', filters, serialized_liked_conversations,
                                            search_message=f"No conversations found for search term: '{filters.search}'")

    return render_conversation_template('conversation-liked.html', filters, serialized_liked_conversations,
                                        liked_conversations_count=liked_conversations_count,
                                        liked_conversations=serialized_liked_conversations)


@llm_conversation_bp.route("/convers-head-tail")
def convers_head_tail():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    filters = ConversationFilters(
        owner_id=current_user.id,
        limit=request.args.get('limit', default=3, type=int),
        offset=request.args.get('offset', default=0, type=int),
        search=request.args.get('search', default=None, type=str)
    )

    first_conversations = get_conversations(filters)
    filters.order_by_desc = True
    last_conversations = get_conversations(filters)
    serialized_first_conversations = [serialize_conversation(conversation) for conversation in first_conversations]
    serialized_last_conversations = [serialize_conversation(conversation) for conversation in last_conversations]

    conversations_count = Memory.query.filter_by(owner_id=filters.owner_id).count()

    if not (serialized_first_conversations or serialized_last_conversations):
        return render_conversation_template('conversation-head-tail.html', filters, [],
                                            search_message=f"No conversations found for search term: '{filters.search}'")

    return render_conversation_template('conversation-head-tail.html', filters, serialized_first_conversations,
                                        first_conversations=serialized_first_conversations,
                                        last_conversations=serialized_last_conversations,
                                        conversations_count=conversations_count)


@llm_conversation_bp.route('/conversation-show-history')
def show_story():
    if current_user.is_authenticated:
        filters = ConversationFilters(
            owner_id=current_user.id,
            limit=request.args.get('limit', default=3, type=int),
            offset=request.args.get('offset', default=None, type=int),
            search=request.args.get('search', default=None, type=str),
            order_by_desc=True
        )

        memory_load = get_conversations(filters)
        serialized_memory_load = [serialize_conversation(memory, last_summary_only=True) for memory in memory_load]

        if memory_load:
            memory_buffer = f'- {current_user.name}(owner_id:{filters.owner_id}):\n\n'
            memory_buffer += '\n\n'.join(
                [f'- Conversation ID: {memory.id}\n\n- {memory.user_name}: {memory.user_message}\n\n'
                 f'·SìįSí·Dbt·: {memory.llm_response}\n\n- Created at: { memory.created_at.strftime("%Y-%m-%d %H:%M:%S") }\n\n'
                 f'' + '-' * 19 for memory in memory_load]
            )

            summary_conversations = '\n\n'.join([memory.conversations_summary.split('\n')[-1] for memory in memory_load])

            return render_template('conversation-show-history.html',
                                   current_user=current_user, owner_id=filters.owner_id,
                                   memory_load=memory_load, memory_buffer=memory_buffer,
                                   summary_conversations=summary_conversations,
                                   serialized_memory_load=serialized_memory_load,
                                   limit=filters.limit, offset=filters.offset, search=filters.search,
                                   date=datetime.now().strftime("%a %d %B %Y"))
        else:
            return render_template('conversation-show-history.html', current_user=current_user, owner_id=filters.owner_id,
                                   limit=filters.limit, offset=filters.offset, search=filters.search,
                                   search_message=f"No conversations found for search term: '{filters.search}'",
                                   date=datetime.now().strftime("%a %d %B %Y"))
    else:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))


@llm_conversation_bp.route('/update-like/<int:conversation_id>', methods=['POST'])
def update_like(conversation_id):
    liked = request.json.get('liked')
    conversation = db.session.get(Memory, conversation_id)
    conversation.liked = liked
    db.session.add(conversation)
    db.session.commit()
    return 'Liked status updated successfully', 200


@llm_conversation_bp.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    filters = ConversationFilters(owner_id=current_user.id)
    conversations = get_conversations(filters)
    serialized_conversations = [serialize_conversation(conversation) for conversation in conversations]

    all_users = User.query.all()
    all_themes = Theme.query.all()
    all_messages = Message.query.all()

    database_form = DatabaseForm()

    memory_tests = MemoryTest.query.all()
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
                           serialized_memory_tests=serialized_memory_tests, all_blog_potos=BlogPost.query.all(),
                           all_website_reviews=WebsiteReview.query.all(), all_drawing_images=DrawingDatabase.query.all())
