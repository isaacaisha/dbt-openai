from flask import Blueprint, render_template, flash, url_for, redirect, request
from flask_login import current_user
from datetime import datetime

from app.databases.database import get_db
from app.forms.app_forms import ConversationIdForm, DeleteForm
from app.models.memory import Memory, db

conversation_functionality_bp = Blueprint('conversation_function', __name__)


@conversation_functionality_bp.route('/select-conversation-id', methods=['GET', 'POST'])
def select_conversation():
    select_conversation_form = ConversationIdForm()

    if request.method == "POST" and select_conversation_form.validate_on_submit():
        print(f"Form data: {select_conversation_form.data}")

        # Retrieve the selected conversation ID
        selected_conversation_id = select_conversation_form.conversation_id.data

        # Construct the URL string for the 'get_conversation' route
        url = url_for('get_conversation', conversation_id=selected_conversation_id)
        return redirect(url)
    else:
        return render_template('conversation-by-id.html',
                               select_conversation_form=select_conversation_form, current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@conversation_functionality_bp.route('/conversation/<int:conversation_id>')
def get_conversation(conversation_id):
    # conversation_ = Memory.query.filter_by(id=conversation_id).first()

    with get_db() as db:
        # conversation_ = Memory.query.filter_by(id=conversation_id).first()
        conversation_ = db.query(Memory).filter_by(id=conversation_id).first()

    try:
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
    except Exception as err:
        print(f"Unexpected {err}, {type(err)}")
        flash(f'😂RETRY🤣')
        flash('Or Please log in to access this page.')
        # flash(f'Error: {err}.')
        return redirect(url_for('select_conversation'))
    else:
        # Format created_at timestamp
        formatted_created_at = conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S")
        return render_template('conversation-details.html', current_user=current_user,
                               conversation_=conversation_, formatted_created_at=formatted_created_at,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))


@conversation_functionality_bp.route('/delete-conversation', methods=['GET', 'POST'])
def delete_conversation():
    delete_conversation_form = DeleteForm()

    try:
        if request.method == "POST" and delete_conversation_form.validate_on_submit():
            # Get the conversation_id from the form
            conversation_id = delete_conversation_form.conversation_id.data
            # Query the database to get the conversation to be deleted
            conversation_to_delete = Memory.query.filter_by(id=conversation_id).first()  # Use Memory.query directly
            # Check if the conversation exists
            if not conversation_to_delete:
                return render_template('conversation-delete-not-found.html', current_user=current_user,
                                       conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))
            # Check if the current user is the owner of the conversation
            if conversation_to_delete.owner_id != current_user.id:
                return render_template('conversation-delete-forbidden.html', current_user=current_user,
                                       conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))
            else:
                # Delete the conversation
                db.session.delete(conversation_to_delete)
                db.session.commit()
                flash(f'Conversation with ID: 🔥{conversation_id}🔥 deleted 😎')
                return redirect(url_for('delete_conversation'))
        return render_template('conversation-delete.html', date=datetime.now().strftime("%a %d %B %Y"),
                               current_user=current_user, delete_conversation_form=delete_conversation_form)
    except Exception as err:
        flash(f'🤣RETRY😂')
        flash('Or Please log in to access this page.')
        # flash(f'Error: {err}.')
        print(f"Unexpected {err}, {type(err)}")
        return redirect(url_for('delete_conversation'))
