from datetime import datetime

import flask_wtf
from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import current_user
from werkzeug.exceptions import InternalServerError, BadRequest


errors_confi_bp = Blueprint('errors', __name__)


def configure_error_handlers():
    # -------------------------------------- @app.errorhandler functions ----------------------------------------------#
    @errors_confi_bp.errorhandler(InternalServerError)
    def handle_internal_server_error(err):
        # Get the URL of the request that caused the error
        referring_url = request.referrer
        flash(f"RETRY (InternalServerError) ¡!¡")
        print(f"InternalServerError ¡!¡ Unexpected {err=}, {type(err)=}")

        # Redirect the user back to the page that produced the error, or a default page if the referrer is not available
        return redirect(referring_url or url_for('authentication_error'))  # , 500

    @errors_confi_bp.errorhandler(BadRequest)
    def handle_bad_request(err):
        # Get the URL of the request that caused the error
        referring_url = request.referrer
        flash(f"RETRY (BadRequest) ¡!¡")
        print(f"BadRequest ¡!¡ Unexpected {err=}, {type(err)=}")

        # Redirect the user back to the page that produced the error, or a default page if the referrer is not available
        return redirect(referring_url or url_for('authentication_error'))  # , 400

    @errors_confi_bp.errorhandler(flask_wtf.csrf.CSRFError)
    def handle_csrf_error(err):
        # Get the URL of the request that caused the error
        referring_url = request.referrer
        flash(f"RETRY (CSRFError) ¡!¡")
        print(f"CSRFError ¡!¡ Unexpected {err=}, {type(err)=}")

        # Redirect the user back to the page that produced the error, or a default page if the referrer is not available
        return redirect(referring_url or url_for('authentication_error'))  # , 401

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
