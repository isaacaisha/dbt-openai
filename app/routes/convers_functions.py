from flask import Blueprint, render_template, flash, url_for, redirect, request
from flask_login import current_user
from datetime import datetime

from app.app_forms import DatabaseForm, ConversationIdForm, DeleteForm
from app.memory import Memory, User, Theme, Message, MemoryTest, BlogPost, PortfolioReview, db


conversation_functionality_bp = Blueprint('conversation_function', __name__)

# Define the table mapping
TABLE_MAPPING = {
    'Memory': Memory,
    'User': User,
    'Theme': Theme,
    'Message': Message,
    'MemoryTest': MemoryTest,
    'BlogPost': BlogPost,
    'PortfolioReview': PortfolioReview,
}


@conversation_functionality_bp.route('/select-conversation-id', methods=['GET', 'POST'])
def select_conversation():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    select_conversation_form = ConversationIdForm()

    if request.method == "POST":
        print(f"Form data: {select_conversation_form.data}")

        # Retrieve the selected conversation ID
        selected_conversation_id = select_conversation_form.conversation_id.data

        # Construct the URL string for the 'get_conversation' route
        url = url_for('conversation_function.get_conversation', conversation_id=selected_conversation_id)
        return redirect(url)
    else:
        return render_template('conversation-by-id.html',
                               select_conversation_form=select_conversation_form, current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@conversation_functionality_bp.route('/conversation/<int:conversation_id>')
def get_conversation(conversation_id):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    conversation_ = db.session.get(Memory, conversation_id)
    if not conversation_:
        # Conversation isn't found, return a not found message
        return render_template('conversation-not-found.html', current_user=current_user,
                               conversation_=conversation_, conversation_id=conversation_id,
                               date=datetime.now().strftime("%a %d %B %Y"))
    
    if conversation_.owner_id != current_user.id:
        # User doesn't have access, return a forbidden message
        return render_template('conversation-forbidden.html', current_user=current_user,
                               conversation_=conversation_, conversation_id=conversation_id,
                               date=datetime.now().strftime("%a %d %B %Y"))
    else:
        # Format created_at timestamp
        formatted_created_at = conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S")
        return render_template('conversation-details.html', current_user=current_user,
                               conversation_=conversation_, formatted_created_at=formatted_created_at,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))


@conversation_functionality_bp.route('/delete-conversation', methods=['GET', 'POST'])
def delete_conversation():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    delete_conversation_form = DeleteForm()

    if request.method == "POST":
        # Get the conversation_id from the form
        conversation_id = delete_conversation_form.conversation_id.data
        
        # Query the database to get the conversation to be deleted
        conversation_to_delete = db.session.get(Memory, conversation_id)
        # Check if the conversation exists
        if not conversation_to_delete:
            return render_template('conversation-not-found.html', current_user=current_user,
                                   conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))
        # Check if the current user is the owner of the conversation
        if conversation_to_delete.owner_id != current_user.id:
            return render_template('conversation-forbidden.html', current_user=current_user,
                                   conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))
        else:
            # Delete the conversation
            db.session.delete(conversation_to_delete)
            db.session.commit()
            flash(f'Conversation with ID: 🔥{conversation_id}🔥 deleted 😎')
            return redirect(url_for('conversation_function.delete_conversation'))
    return render_template('conversation-delete.html', current_user=current_user,
                           delete_conversation_form=delete_conversation_form,
                           date=datetime.now().strftime("%a %d %B %Y"))


@conversation_functionality_bp.route('/delete-data', methods=['GET', 'POST'])
def delete_data():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    database_form = DatabaseForm()

    if request.method == "POST":
        if database_form.validate_on_submit():
            # Get the data_id and database name from the form
            db_data_name = database_form.database_name.data
            db_data_id = database_form.data_id.data

            # Get the corresponding model class
            model_class = TABLE_MAPPING.get(db_data_name)
            if model_class is None:
                flash(f"Invalid database name: {db_data_name}")
                return redirect(url_for('conversation_function.delete_data'))
            
            # Query the database to get the data to be deleted
            data_to_delete = db.session.get(model_class, db_data_id)
            
            # Check if the data exists
            if not data_to_delete:
                flash('No Data to Delete')
            else:
                # Delete the data
                db.session.delete(data_to_delete)
                db.session.commit()
                flash(f'Database: 🔥{db_data_name}🔥 Data with ID: 🔥{db_data_id}🔥 Data Deleted 😎')
                return redirect(url_for('llm_conversation.get_conversations_jsonify'))
    return render_template('database-conversations.html', current_user=current_user,
                           database_form=database_form, date=datetime.now().strftime("%a %d %B %Y"))
