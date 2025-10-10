from flask import (Blueprint, render_template)

foreign_agents_bp = Blueprint('foreign_agents', __name__, template_folder='../../templates')

@foreign_agents_bp.route('/fl')
def fl():
    return render_template('foreign-agents/fl.html')

@foreign_agents_bp.route('/ul')
def ul():
    return render_template('foreign-agents/ul.html')
