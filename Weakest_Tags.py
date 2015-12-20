# -*- coding: utf-8 -*-

from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from collections import defaultdict
import operator

TOP_WEAKEST = 5

def calculate_and_show_weakest_tags():
    top, is_ok = QInputDialog.getInteger(mw, _("Top lapses count"),
                                         _("Number of weakest tags to show (0 means all):"),
                                        TOP_WEAKEST, 0)

    top = top if is_ok else TOP_WEAKEST

    current_deck = mw.col.decks.current()

    query = '''SELECT
        c.id AS card_id,
        c.lapses as lapses,
        n.id AS note_id,
        n.tags as tags

    FROM cards c
    INNER JOIN notes n ON c.nid=n.id
    WHERE c.did={};'''.format(current_deck['id'])

    tags_lapses = defaultdict(int)

    for card_id, card_lapses, note_id, tags_str in mw.col.db.execute(query):
        tags = tags_str.split() if tags_str else []

        for tag in tags:
            tags_lapses[tag] += card_lapses

    sorted_tags_lapses = sorted(tags_lapses.items(), key=operator.itemgetter(1), reverse=True)
    sorted_tags_lapses = sorted_tags_lapses[:top] if top else sorted_tags_lapses

    if sorted_tags_lapses and sorted_tags_lapses[0][1] == 0:
        message = ('Wow, looks like you have no lapses at all for deck "{}".'
            ' Congrats!'.format(current_deck['name']))
    else:
        message = [
            'Here is your weakes tags  for deck "{}":'.format(current_deck['name']),
            ''
        ]

        for tag, count in sorted_tags_lapses:
            message.append('{}, lapses {}'.format(tag, count))

        message = '\n'.join(message)

    QMessageBox.information(mw, _('Weakest tags'), message)

action = QAction("Weakest Tags", mw)
mw.connect(action, SIGNAL("triggered()"), calculate_and_show_weakest_tags)
mw.form.menuTools.addAction(action)
