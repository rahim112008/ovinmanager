# Dashboard Page

from flask import Blueprint, render_template

# Initialize the Blueprint
page_dashboard = Blueprint('page_dashboard', __name__)

@page_dashboard.route('/dashboard')
def dashboard():
    """Render the dashboard page."""
    return render_template('dashboard.html')

# You can add more functionalities such as graph displays, user statistics, etc.