'''
NER annotator
'''


import sys
import os
import argparse
import json
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
    QMessageBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QApplication
)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt


# Input/output formats
VALID_IN_FMT = ('.txt')
VALID_OUT_FMT = ('.json')

# Output table labels
ENTITY_LABEL = 'Entity'
SELECTION_START_LABEL = 'Selection start'
SELECTION_END_LABEL = 'Selection end'


def is_file_valid(path, valid_fmts):
    '''
    Check if the given file is valid
    '''
    if not os.path.isfile(path):
        raise Exception(
            'The input path you entered does not exist or is not a file'
        )

    _, file_extension = os.path.splitext(path)
    if file_extension not in valid_fmts:
        raise Exception(
            'The input file you entered has an invalid extension. '
            f'Please enter a file with one of the following formats: {VALID_IN_FMT}'
        )

    return True


def show_warning(text, informative):
    '''
    Shows a warning message
    '''
    warning_dialog = QMessageBox()
    warning_dialog.setIcon(QMessageBox.Warning)
    warning_dialog.setText(text)
    warning_dialog.setInformativeText(informative)
    warning_dialog.setWindowTitle("Warning")
    warning_dialog.exec_()


def show_error(text, informative):
    '''
    Shows a error message
    '''
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Critical)
    error_dialog.setText(text)
    error_dialog.setInformativeText(informative)
    error_dialog.setWindowTitle("Error")
    error_dialog.exec_()


class NERAnnotator(QMainWindow):
    '''
    Main window
    '''

    def __init__(self, input_file, output_file, entities):
        # Window settings
        QMainWindow.__init__(self)
        self.setWindowTitle(self.__class__.__name__)
        self.setFocusPolicy(Qt.StrongFocus)

        # Instance variables
        self.input_file = input_file
        self.output_file = output_file
        self.entities = entities
        self.annotations = []
        self.current_line = 0

        # Stretch widgets
        self.widget = QWidget(self)
        self.size_policy = QSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.size_policy.setHorizontalStretch(0)
        self.size_policy.setVerticalStretch(0)
        self.widget.setSizePolicy(self.size_policy)

        # Main layout
        self.main_layout = QHBoxLayout(self.widget)
        self.left_layout = QVBoxLayout()
        self.left_top_layout = QVBoxLayout()
        self.left_bottom_layout = QHBoxLayout()
        self.right_layout = QVBoxLayout()

        # Left top layout
        self.content_label = QLabel('Content')
        self.content_text = QPlainTextEdit(self.input_file[0])
        self.content_text.setReadOnly(True)
        self.output_label = QLabel('Output')
        self.output_table = QTableWidget(0, 3)
        self.output_table_labels = {
            ENTITY_LABEL: 0,
            SELECTION_START_LABEL: 1,
            SELECTION_END_LABEL: 2
        }
        self.output_table.setHorizontalHeaderLabels(
            self.output_table_labels.keys()
        )
        self.left_top_layout.addWidget(self.content_label, 0, Qt.AlignCenter)
        self.left_top_layout.addWidget(self.content_text, 0, Qt.AlignCenter)
        self.left_top_layout.addWidget(self.output_label, 0, Qt.AlignCenter)
        self.left_top_layout.addWidget(self.output_table, 0, Qt.AlignCenter)

        # Left bottom layout
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

        # Left layout
        self.left_layout.addLayout(self.left_top_layout)
        self.left_layout.addLayout(self.left_bottom_layout)

        # Right layout
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

        # Main layout
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addLayout(self.right_layout)
        self.widget.setLayout(self.main_layout)
        self.setCentralWidget(self.widget)

    def skip(self):
        '''
        Show the next line of the training file
        '''
        if self.current_line == len(self.input_file) - 1:
            show_warning(
                text='No more lines in the input file',
                informative='You should save the results using the "stop" button'
            )
            return
        self.current_line += 1
        self.content_text.clear()
        self.content_text.insertPlainText(self.input_file[self.current_line])
        self.output_table.setRowCount(0)

    def record(self):
        '''
        Save the current annotations
        '''
        text = self.content_text.toPlainText()
        entities = []
        for i in range(self.output_table.rowCount()):
            entities.append([
                int(self.output_table.item(
                    i, self.output_table_labels[SELECTION_START_LABEL]
                ).text()),
                int(self.output_table.item(
                    i,  self.output_table_labels[SELECTION_END_LABEL]
                ).text()),
                self.output_table.item(
                    i, self.output_table_labels[ENTITY_LABEL]
                ).text()
            ])
        self.annotations.append(
            {
                'content': text,
                'entities': entities
            }
        )

    def next(self):
        '''
        Save the current annotations and go to the next line
        '''
        self.record()
        self.skip()

    def stop(self):
        '''
        Complete the annotating process
        '''
        self.record()
        try:
            open(self.output_file, 'w').write(json.dumps(self.annotations))
        except Exception as err:
            show_error(
                text='An error occurred while saving the output file',
                informative=str(err)
            )
            return
        self.close()

    def add_entity(self, entity):
        '''
        Add the selected entity
        '''
        cursor = self.content_text.textCursor()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        if selection_end - selection_start > 0:
            rows = self.output_table.rowCount()
            self.output_table.insertRow(rows)
            self.output_table.setItem(
                rows,
                self.output_table_labels[SELECTION_START_LABEL],
                QTableWidgetItem(str(selection_start))
            )
            self.output_table.setItem(
                rows,
                self.output_table_labels[SELECTION_END_LABEL],
                QTableWidgetItem(str(selection_end))
            )
            self.output_table.setItem(
                rows,
                self.output_table_labels[ENTITY_LABEL],
                QTableWidgetItem(entity)
            )


def parse_args():
    '''
    CLI argument parser
    '''
    parser = argparse.ArgumentParser(
        prog='ner-annotator', description='NER annotator')
    parser.add_argument(
        dest='input', action='store',
        type=str, help='path to the training text file'
    )
    parser.add_argument(
        dest='entities', action='store', nargs='+',
        type=str, help='list of entities to be classified'
    )
    parser.add_argument(
        '-o', '--output', dest='output', action='store',
        type=str, help='path to the output file'
    )
    return parser


if __name__ == "__main__":
    parser = parse_args()
    args = parser.parse_args()

    if is_file_valid(args.input, VALID_IN_FMT):
        input_file = open(args.input, 'r').read().splitlines()
        if args.output is None:
            args.output = (
                os.path.abspath(os.path.join(
                    os.path.dirname(args.input), 'output.json'
                ))
            )
        if is_file_valid(args.output, VALID_OUT_FMT):
            app = QApplication(sys.argv)
            window = NERAnnotator(input_file, args.output, args.entities)
            window.show()
            sys.exit(app.exec_())
