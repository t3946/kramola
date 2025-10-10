from flask import (Blueprint, render_template)

from services.words_list.list_companies import ListCompanies
from services.words_list.list_persons import ListPersons

foreign_agents_bp = Blueprint('foreign_agents', __name__, template_folder='../../templates')

@foreign_agents_bp.route('/fl')
def fl():
    lp = ListPersons()
    words = lp.load()

    return render_template('foreign-agents/fl.html', words=words)

@foreign_agents_bp.route('/ul')
def ul():
    lc = ListCompanies()
    words = lc.load()

    return render_template('foreign-agents/ul.html', words=words)
