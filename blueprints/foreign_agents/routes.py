from flask import (Blueprint, render_template)

from services.words_list.list_inagents_fiz import ListInagentsFIZ
from services.words_list.list_inagents_ur import ListInagentsUR
from services.words_list.list_profanity import ListProfanity
from services.words_list.list_prohibited_substances import ListProhibitedSubstances
from services.words_list.list_swear_words import ListSwearWords
from services.words_list.list_extremists_terrorists import ListExtremistsTerrorists

foreign_agents_bp = Blueprint('foreign_agents', __name__, template_folder='../../templates')

@foreign_agents_bp.route('/fl')
def fl():
    lp = ListInagentsFIZ()
    phrases = lp.load()
    words = [phrase.phrase for phrase in phrases]
    changes_sorted: dict = {}

    return render_template('foreign-agents/fl.html', words=words, changes=changes_sorted)

@foreign_agents_bp.route('/ul')
def ul():
    lc = ListInagentsUR()
    phrases = lc.load()
    words = [phrase.phrase for phrase in phrases]
    changes_sorted: dict = {}

    return render_template('foreign-agents/ul.html', words=words, changes=changes_sorted)

@foreign_agents_bp.route('/profanity')
def profanity():
    lp = ListProfanity()
    phrases = lp.load()
    words = [phrase.phrase for phrase in phrases]

    return render_template('foreign-agents/profanity.html', words=words)

@foreign_agents_bp.route('/prohibited-substances')
def prohibited_substances():
    lps = ListProhibitedSubstances()
    phrases = lps.load()
    words = [phrase.phrase for phrase in phrases]

    return render_template('foreign-agents/prohibited_substances.html', words=words)

@foreign_agents_bp.route('/swear-words')
def swear_words():
    lsw = ListSwearWords()
    phrases = lsw.load()
    words = [phrase.phrase for phrase in phrases]

    return render_template('foreign-agents/swear_words.html', words=words)


@foreign_agents_bp.route('/extremists-terrorists')
def extremists_terrorists():
    let = ListExtremistsTerrorists()
    phrases = let.load()
    words = [phrase.phrase for phrase in phrases]

    return render_template('foreign-agents/extremists_terrorists.html', words=words)
