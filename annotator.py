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
    QLabel,
    QPushButton,
    QMessageBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QHeaderView,
    QApplication
)
from PyQt5.QtCore import Qt


# Input/output formats
VALID_IN_FMT = ('.txt')
VALID_OUT_FMT = ('.json')

# Output table labels
ENTITY_LABEL = 'Entity'
SELECTION_START_LABEL = 'Selection start'
SELECTION_END_LABEL = 'Selection end'

# CSS
STYLE = open('style.css').read()


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
        self.resize(1200, 800)
        self.setWindowTitle(self.__class__.__name__)
        self.setFocusPolicy(Qt.StrongFocus)

        # Instance variables
        self.input_file = input_file
        self.output_file = output_file
        self.entities = entities
        self.annotations = []
        self.current_line = 0

        # Main layout
        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet(STYLE)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.left_widget = QWidget(self.central_widget)
        self.left_layout = QVBoxLayout(self.left_widget)
        self.right_widget = QWidget(self.central_widget)
        self.right_layout = QVBoxLayout(self.right_widget)

        # Left layout
        self.content_label = QLabel(self.left_widget)
        self.content_label.setText('Content')
        self.content_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.content_text = QPlainTextEdit(
            self.input_file[0], self.left_widget
        )
        self.content_text.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.content_text.setReadOnly(True)
        self.output_label = QLabel(self.left_widget)
        self.output_label.setText('Output')
        self.output_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.output_table = QTableWidget(0, 3, self.left_widget)
        self.output_table.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.output_table_labels = {
            ENTITY_LABEL: 0,
            SELECTION_START_LABEL: 1,
            SELECTION_END_LABEL: 2
        }
        self.output_table.setHorizontalHeaderLabels(
            self.output_table_labels.keys()
        )
        self.output_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.skip_button = QPushButton('Skip', self.left_widget)
        self.skip_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.skip_button.clicked.connect(self.skip)
        self.next_button = QPushButton('Next', self.left_widget)
        self.next_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.next_button.clicked.connect(self.next)
        self.stop_button = QPushButton('Stop', self.left_widget)
        self.stop_button.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.stop_button.clicked.connect(self.stop)
        self.left_layout.addWidget(self.content_label, 0, Qt.AlignCenter)
        self.left_layout.addWidget(self.content_text)
        self.left_layout.addWidget(self.output_label, 0, Qt.AlignCenter)
        self.left_layout.addWidget(self.output_table)
        self.left_layout.addWidget(self.skip_button)
        self.left_layout.addWidget(self.next_button)
        self.left_layout.addWidget(self.stop_button)

        # Right layout
        self.entities_label = QLabel(self.right_widget)
        self.entities_label.setText('Entities')
        self.entities_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.right_layout.addWidget(self.entities_label, 0, Qt.AlignCenter)
        self.entities_buttons = {}
        for entity in self.entities:
            self.entities_buttons[entity] = QPushButton(
                entity, self.right_widget
            )
            self.entities_buttons[entity].setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.entities_buttons[entity].clicked.connect(
                partial(self.add_entity, entity)
            )
            self.right_layout.addWidget(self.entities_buttons[entity])

        # Main layout
        self.main_layout.addWidget(self.left_widget)
        self.main_layout.addWidget(self.right_widget)
        self.setCentralWidget(self.central_widget)

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
        entities = []
        for i in range(self.output_table.rowCount()):
            ent = self.output_table.item(
                i, self.output_table_labels[ENTITY_LABEL]
            ).text()
            ss = self.output_table.item(
                i,  self.output_table_labels[SELECTION_START_LABEL]
            ).text()
            se = self.output_table.item(
                i,  self.output_table_labels[SELECTION_END_LABEL]
            ).text()
            if ent and ss.isdigit() and se.isdigit():
                entities.append([int(ss), int(se), ent])
        if entities:
            self.annotations.append(
                {
                    'content': self.content_text.toPlainText(),
                    'entities': entities
                }
            )

    def next(self):
        '''
        Save the current annotations and go to the next line
        '''
        self.record()
        self.skip()

    def save(self):
        '''
        Save annotations to the output file
        '''
        try:
            open(self.output_file, 'w').write(json.dumps(self.annotations))
        except Exception as err:
            show_error(
                text='An error occurred while saving the output file',
                informative=str(err)
            )

    def stop(self):
        '''
        Complete the annotating process
        '''
        self.record()
        self.save()
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

    def closeEvent(self, event):
        self.record()
        if self.annotations:
            quit_msg = "You have unsaved work. Would you like to save it before leaving?"
            reply = QMessageBox.question(
                self, 'Save before exit', quit_msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save()
                event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            quit_msg = "Are you sure you want to exit the program?"
            reply = QMessageBox.question(
                self, 'Exit', quit_msg, QMessageBox.Yes, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


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
        elif not is_file_valid(args.output, VALID_OUT_FMT):
            raise
        app = QApplication(sys.argv)
        window = NERAnnotator(input_file, args.output, args.entities)
        window.show()
        sys.exit(app.exec_())
