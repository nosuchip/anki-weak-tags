# -*- coding: utf-8 -*-

from aqt import mw
from aqt.utils import showInfo
from aqt.qt import *
from collections import defaultdict
import operator

TOP_WEAKEST = 10

def calculate_and_show_weakest_tags():
    class QWeakestTagsQueryDialog(QDialog):
        def __init__(self, parent=None):
            QDialog.__init__(self, parent)

            self.layout = QFormLayout(self)

            self.tags_count_widget = QLineEdit(self)
            self.tags_count_widget.setInputMask('9999')
            self.tags_count_widget.setText(str(TOP_WEAKEST))
            label = QLabel('Number of tags to show:')
            label.setToolTip('Only number are available')
            self.layout.addRow(label, self.tags_count_widget)

            self.ignored_tags_widget = QLineEdit(self)
            label = QLabel('Ignored tags (comma separated):')
            label.setToolTip('These tags will be excluded from resultset')
            self.layout.addRow(label, self.ignored_tags_widget)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            self.layout.addRow(button_box)

        @property
        def tags_count(self):
            return int(self.tags_count_widget.text())

        @property
        def ignored_tags(self):
            text = self.ignored_tags_widget.text().split()
            return [t.strip() for t in text if t.strip()]

    class QWeakestTagsResultDialog(QDialog):
        def __init__(self, parent=None):
            QDialog.__init__(self, parent)

            width = 500
            height = 500

            self.setGeometry(
                parent.x() + parent.width()/2 - width/2,
                parent.y() + parent.height()/2 - height/2,
                width, height
            );

            self.layout = QVBoxLayout(self)

            layout_top = QHBoxLayout()
            self.cards_lapses_widget = QLabel('?')
            layout_top.addWidget(QLabel('<b>Total cards with lapses:</b>'))
            layout_top.addWidget(self.cards_lapses_widget)
            self.layout.addLayout(layout_top)

            self.layout.addSpacing(10)

            self.layout.addWidget(QLabel('<b>Weakest tags for your deck</b>'))

            self.table_widget = QTableWidget()
            self.table_widget.horizontalHeader().setResizeMode(QHeaderView.Stretch);
            self.layout.addWidget(self.table_widget)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok, parent=self)
            button_box.accepted.connect(self.accept)
            self.layout.addWidget(button_box)

        def set_cards_with_lapses(self, value):
            self.cards_lapses_widget.setText(str(value))

        def set_tags_with_lapses(self, values):
            t = self.table_widget

            t.clear()
            t.setRowCount(len(values))
            t.setColumnCount(2)

            t.setHorizontalHeaderLabels(['Tag name', 'Lapses count'])

            try:
                for row_number, row in enumerate(values):
                    tag = row[0]
                    lapses = row[1]

                    t.setItem(row_number, 0, QTableWidgetItem(str(tag)))
                    t.setItem(row_number, 1, QTableWidgetItem(str(lapses)))
            except Exception as ex:
                print "Error occures:", ex

    query_dialog = QWeakestTagsQueryDialog(mw)

    if query_dialog.exec_() == QDialog.Rejected:
        return

    result_dialog = QWeakestTagsResultDialog(mw)
    current_deck = mw.col.decks.current()

    query = '''SELECT
        c.id AS card_id,
        c.lapses as lapses,
        n.id AS note_id,
        n.tags as tags

    FROM cards c
    INNER JOIN notes n ON c.nid=n.id
    WHERE c.did=?;'''

    tags_lapses = defaultdict(int)

    for card_id, card_lapses, note_id, tags_str in mw.col.db.execute(query, current_deck['id']):
        tags = tags_str.split() if tags_str else []

        for tag in tags:
            tags_lapses[tag] += card_lapses

    sorted_tags_lapses = sorted(tags_lapses.items(), key=operator.itemgetter(1), reverse=True)

    ignored_tags = query_dialog.ignored_tags
    sorted_tags_lapses = [t for t in sorted_tags_lapses if t[0] not in ignored_tags]

    top = query_dialog.tags_count
    sorted_tags_lapses = sorted_tags_lapses[:top] if top else sorted_tags_lapses

    if sorted_tags_lapses and sorted_tags_lapses[0][1] == 0:
       result_dialog.set_tags_with_lapses([('No lapses at all!')])
    else:
        result_dialog.set_tags_with_lapses(sorted_tags_lapses)

    query = '''SELECT COUNT(c.id) FROM cards c
    WHERE c.lapses IS NOT NULL AND c.lapses>0 AND c.did=?'''

    card_with_lapses = mw.col.db.scalar(query, current_deck['id'])
    result_dialog.set_cards_with_lapses(card_with_lapses)

    result_dialog.setWindowTitle('Result for deck "{}"'.format(current_deck['name']))

    result_dialog.show()


action = QAction("Weakest Tags", mw)
mw.connect(action, SIGNAL("triggered()"), calculate_and_show_weakest_tags)
mw.form.menuTools.addAction(action)
