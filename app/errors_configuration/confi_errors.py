from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user


errors_confi_bp = Blueprint('errors', __name__)


def configure_error_handlers():
    # -------------------------------------- @app.errorhandler pages --------------------------------------------------#
    @errors_confi_bp.route('/authentication-error', methods=['GET', 'POST'])
    def authentication_error():
        return render_template('authentication-error.html', current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y")), 401

    @errors_confi_bp.route('/conversation-forbidden/<int:conversation_id>', methods=['GET', 'POST'])
    def conversation_forbidden(conversation_id=None):
        return render_template('conversation-forbidden.html', current_user=current_user,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y")), 403

    @errors_confi_bp.route('/conversation-not-found/<int:conversation_id>', methods=['GET', 'POST'])
    def conversation_not_found(conversation_id):
        return render_template('conversation-not-found.html', current_user=current_user,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y")), 404

    @errors_confi_bp.route('/conversation-delete-forbidden/<int:conversation_id>', methods=['GET', 'POST'])
    def conversation_delete_forbidden(conversation_id):
        return render_template('conversation-delete-forbidden.html', current_user=current_user,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y")), 403

    @errors_confi_bp.route('/conversation-delete-not-found/<int:conversation_id>', methods=['GET', 'POST'])
    def conversation_delete_not_found(conversation_id):
        return render_template('conversation-delete-not-found.html', current_user=current_user,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y")), 404


configure_error_handlers()
