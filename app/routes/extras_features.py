from flask import Blueprint, render_template
from datetime import datetime


features_extras_bp = Blueprint('extras_features', __name__)


@features_extras_bp.route("/extras-features-home", methods=["GET"])
def extras_features_home():
    return render_template('extras-features.html', date=datetime.now().strftime("%a %d %B %Y"))

@features_extras_bp.route("/blog-generator", methods=["GET", "POST"])
def blog_generator():
    return render_template('generated-blog.html', date=datetime.now().strftime("%a %d %B %Y"))

