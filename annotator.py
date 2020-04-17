'''
NER annotator
'''


import sys
import os
import argparse
from functools import partial

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QLineEdit,
    QLabel,
    QPushButton,
    QApplication
)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt


class NERAnnotator(QMainWindow):
    '''
    Main window
    '''

    def __init__(self, train_text, entities):
        QMainWindow.__init__(self)
        self.resize(350, 250)
        self.setWindowTitle(self.__class__.__name__)
        self.setFocusPolicy(Qt.StrongFocus)

        self.train_text = train_text
        self.entities = entities
        self.annotations = []
        self.current_line = 0

        self.widget = QWidget(self)
        self.main_layout = QHBoxLayout(self.widget)
        self.left_layout = QVBoxLayout()
        self.left_top_layout = QVBoxLayout()
        self.left_bottom_layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()

        self.content_label = QLabel('Content')
        self.content_text = QPlainTextEdit(self.train_text[0])
        self.output_label = QLabel('Output')
        self.output_text = QPlainTextEdit()
        self.left_top_layout.addWidget(self.content_label, 0, Qt.AlignCenter)
        self.left_top_layout.addWidget(self.content_text, 0, Qt.AlignCenter)
        self.left_top_layout.addWidget(self.output_label, 0, Qt.AlignCenter)
        self.left_top_layout.addWidget(self.output_text, 0, Qt.AlignCenter)

        self.skip_button = QPushButton('Skip')
        self.skip_button.clicked.connect(self.skip)
        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.next)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop)
        self.left_bottom_layout.addWidget(self.skip_button, 0, Qt.AlignCenter)
        self.left_bottom_layout.addWidget(self.next_button, 0, Qt.AlignCenter)
        self.left_bottom_layout.addWidget(
            self.stop_button, 0, Qt.AlignCenter
        )

        self.left_layout.addLayout(self.left_top_layout)
        self.left_layout.addLayout(self.left_bottom_layout)

        self.entities_label = QLabel('Entities')
        self.right_layout.addWidget(self.entities_label, 0, Qt.AlignCenter)
        self.entities_buttons = {}
        for entity in self.entities:
            self.entities_buttons[entity] = QPushButton(entity)
            self.entities_buttons[entity].clicked.connect(
                partial(self.add_entity, entity)
            )
            self.right_layout.addWidget(
                self.entities_buttons[entity], 0, Qt.AlignCenter
            )

        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        self.setCentralWidget(self.widget)

    def skip(self):
        self.current_line += 1
        self.content_text.clear()
        self.content_text.insertPlainText(self.train_text[self.current_line])
        self.output_text.clear()

    def record(self):
        text = self.content_text.toPlainText()
        text_entities = self.output_text.toPlainText().splitlines()
        entities = []
        for ent in text_entities:
            splitted_ent = ent.split()
            entities.append([
                int(splitted_ent[1]),
                int(splitted_ent[2]),
                splitted_ent[0]
            ])
        self.annotations.append(
            {
                'content': text,
                'entities': entities
            }
        )

    def next(self):
        self.record()
        self.skip()

    def stop(self):
        self.record()
        print(self.annotations)

    def add_entity(self, entity):
        cursor = self.content_text.textCursor()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        if selection_end - selection_start > 0:
            self.output_text.moveCursor(QTextCursor.End)
            self.output_text.insertPlainText(
                f'{entity} {selection_start} {selection_end}\n'
            )
            self.output_text.moveCursor(QTextCursor.End)


def parse_args():
    '''
    CLI argument parser
    '''
    parser = argparse.ArgumentParser(
        prog='ner-annotator', description='NER annotator')
    parser.add_argument(
        dest='path', action='store',
        type=str, help='path to the training text file'
    )
    parser.add_argument(
        dest='entities', action='store', nargs='+',
        type=str, help='list of entities to be classified'
    )
    return parser


if __name__ == "__main__":
    parser = parse_args()
    args = parser.parse_args()

    valid_fmt = ('.txt')
    if not os.path.isfile(args.path):
        raise Exception(
            'The path you entered does not exist or is not a file'
        )
    _, file_extension = os.path.splitext(args.path)
    if file_extension not in ('.txt'):
        raise Exception(
            'The file you entered has an invalid extension. '
            f'Please enter a file with one of the following formats: {valid_fmt}'
        )

    train_text = open(args.path, 'r').read().splitlines()
    app = QApplication(sys.argv)
    window = NERAnnotator(train_text, args.entities)
    window.show()
    sys.exit(app.exec_())
