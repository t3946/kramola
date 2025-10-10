from flask import (Blueprint, render_template)

foreign_agents_bp = Blueprint('main', __name__, template_folder='../../templates')

@foreign_agents_bp.route('/foreign-agents')
def foreign_agents():
    return render_template('foreign-agents-fl.html')
