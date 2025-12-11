from flask import (Blueprint, render_template)

from services.words_list.list_companies import ListCompanies
from services.words_list.list_persons import ListPersons

foreign_agents_bp = Blueprint('foreign_agents', __name__, template_folder='../../templates')

@foreign_agents_bp.route('/fl')
def fl():
    lp = ListPersons()
    words = lp.load()
    changes = lp.get_changes_json()
    # Sort changes by date (newest first)
    changes_sorted = dict(sorted(changes.items(), key=lambda x: x[0], reverse=True))

    return render_template('foreign-agents/fl.html', words=words, changes=changes_sorted)

@foreign_agents_bp.route('/ul')
def ul():
    lc = ListCompanies()
    words = lc.load()
    changes = lc.get_changes_json()
    # Sort changes by date (newest first)
    changes_sorted = dict(sorted(changes.items(), key=lambda x: x[0], reverse=True))

    return render_template('foreign-agents/ul.html', words=words, changes=changes_sorted)
