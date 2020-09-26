'''
Define the main window
'''


import json
import copy
import math
import random
from functools import partial

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPlainTextEdit,
    QLabel,
    QPushButton,
    QMessageBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QEvent, QSize
from PyQt5.QtGui import QIcon, QTextCursor, QTextCharFormat, QColor

import ner_annotator


class AutoGridLayout(QGridLayout):
    '''
    A grid layout which automatically lays widgets in the right way
    '''

    def __init__(self, num_elements, parent=None):
        QGridLayout.__init__(self, parent)
        self.num_elements = num_elements
        self.row, self.column = 0, 0
        self.num_rows, self.num_columns = self._find_size()

    def _find_size(self):
        '''
        Minimize emptiness, subject to the number of rows and columns 
        being greater than 1, and pick the more square-like option
        if there are several minimizing sizes
        (see https://stackoverflow.com/questions/19538517/find-matrix-dimension-so-as-to-contain-numbers)
        '''
        mm = list(range(2, math.ceil(math.sqrt(self.num_elements)) + 1))[::-1]
        nn = list(map(lambda x: math.ceil(self.num_elements / x), mm))
        excess = list(
            map(lambda xy: xy[0] * xy[1] - self.num_elements, zip(mm, nn))
        )
        ind = min(excess)
        return mm[ind], nn[ind]

    def addNextWidget(self, widget):
        '''
        Add the given widget and respect the computed number
        of rows and columns
        '''
        self.addWidget(widget, self.row, self.column)
        self.column = (self.column + 2) % self.num_columns
        if self.column == 0:
            self.row += 1


def show_dialog(dialog_type, title, text, informative=''):
    '''
    Shows a dialog message
    '''
    dialog = QMessageBox()
    dialog.setIcon(dialog_type)
    dialog.setText(text)
    dialog.setInformativeText(informative)
    dialog.setWindowTitle(title)
    dialog.exec_()


class NERAnnotator(QMainWindow):
    '''
    Main window
    '''

    def __init__(self, input_file, output_file, entities, model_path=None):
        # Window settings
        QMainWindow.__init__(self)
        self.resize(1200, 800)
        self.setWindowTitle(ner_annotator.WINDOW_TITLE)
        self.setFocusPolicy(Qt.StrongFocus)

        # Instance variables
        self.input_file = input_file
        self.output_file = output_file
        self.entities = entities
        self.model = (
            ner_annotator.load_model(model_path) if model_path is not None
            else None
        )
        self.annotations = []
        self.current_line = 0
        self.latest_save = []

        # Main layout
        self.central_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.content_widget = QWidget(self.central_widget)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.entities_widget = QWidget(self.central_widget)
        self.entities_layout = QVBoxLayout(self.entities_widget)
        self.entities_buttons_widget = QWidget(self.entities_widget)
        self.entities_buttons_layout = AutoGridLayout(
            len(entities), self.entities_buttons_widget
        )
        self.output_widget = QWidget(self.central_widget)
        self.output_layout = QVBoxLayout(self.output_widget)
        self.commands_widget = QWidget(self.central_widget)
        self.commands_layout = QHBoxLayout(self.commands_widget)

        # Content section
        self.content_label = QLabel(self.content_widget)
        self.content_label.setText('Content')
        self.content_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.content_text = QPlainTextEdit(
            self.input_file[0], self.content_widget
        )
        self.content_text.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.content_text.setReadOnly(True)
        self.lines_label = QLabel(self.content_widget)
        self.lines_label.setText(f'Line 1/{len(self.input_file)}')
        self.content_layout.addWidget(self.content_label, 0, Qt.AlignCenter)
        self.content_layout.addWidget(self.content_text)
        self.content_layout.addWidget(self.lines_label, 0, Qt.AlignRight)

        # Entities section
        self.entities_label = QLabel(self.entities_widget)
        self.entities_label.setText('Entities')
        self.entities_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.entities_layout.addWidget(self.entities_label, 0, Qt.AlignCenter)
        self.entities_buttons = {}
        for i, entity in enumerate(self.entities):
            text = entity
            if len(self.entities) < 10:
                text = f'{i + 1}. ' + text
            self.entities_buttons[entity] = QPushButton(
                text, self.entities_buttons_widget
            )
            self.entities_buttons[entity].setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.entities_buttons[entity].clicked.connect(
                partial(self.add_selected_entity, entity)
            )
            self.entities_buttons_layout.addNextWidget(
                self.entities_buttons[entity]
            )
        self.entities_layout.addWidget(self.entities_buttons_widget)

        # Output section
        self.output_label = QLabel(self.output_widget)
        self.output_label.setText('Output')
        self.output_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.output_table_labels = {
            ner_annotator.ENTITY_LABEL: 0,
            ner_annotator.VALUE_LABEL: 1,
            ner_annotator.SELECTION_START_LABEL: 2,
            ner_annotator.SELECTION_END_LABEL: 3
        }
        self.output_table = QTableWidget(
            0, len(self.output_table_labels), self.output_widget
        )
        self.output_table.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.output_table.setHorizontalHeaderLabels(
            self.output_table_labels.keys()
        )
        self.output_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.output_table.horizontalHeader().setSectionResizeMode(
            self.output_table_labels[ner_annotator.ENTITY_LABEL], QHeaderView.Stretch
        )
        self.output_table.horizontalHeader().setSectionResizeMode(
            self.output_table_labels[ner_annotator.VALUE_LABEL], QHeaderView.Stretch
        )
        self.output_table.horizontalHeader().setSectionResizeMode(
            self.output_table_labels[ner_annotator.SELECTION_START_LABEL], QHeaderView.ResizeToContents
        )
        self.output_table.horizontalHeader().setSectionResizeMode(
            self.output_table_labels[ner_annotator.SELECTION_END_LABEL], QHeaderView.ResizeToContents
        )
        self.output_layout.addWidget(self.output_label, 0, Qt.AlignCenter)
        self.output_layout.addWidget(self.output_table)

        # Commands sections
        self.prev_button = self.set_button(
            icon_path=ner_annotator.PREV_ICON_PATH,
            function=self.prev,
            parent=self.commands_widget
        )
        if self.model is not None:
            self.classify_button = self.set_button(
                icon_path=ner_annotator.CLASSIFY_ICON_PATH,
                function=self.classify,
                parent=self.commands_widget
            )
        self.next_button = self.set_button(
            icon_path=ner_annotator.NEXT_ICON_PATH,
            function=self.next,
            parent=self.commands_widget
        )
        self.skip_button = self.set_button(
            icon_path=ner_annotator.SKIP_ICON_PATH,
            function=self.skip,
            parent=self.commands_widget
        )
        self.save_button = self.set_button(
            icon_path=ner_annotator.SAVE_ICON_PATH,
            function=self.stop,
            parent=self.commands_widget
        )
        self.commands_layout.addWidget(self.prev_button)
        if self.model is not None:
            self.commands_layout.addWidget(self.classify_button)
        self.commands_layout.addWidget(self.next_button)
        self.commands_layout.addWidget(self.skip_button)
        self.commands_layout.addWidget(self.save_button)

        # Main layout
        self.setCentralWidget(self.central_widget)
        self.main_layout.addWidget(self.content_widget)
        self.main_layout.addWidget(self.entities_widget)
        self.main_layout.addWidget(self.output_widget)
        self.main_layout.addWidget(self.commands_widget)

    def set_button(self, icon_path, function, name="", parent=None):
        '''
        Configures a QPushButton
        '''
        btn = QPushButton(name, parent)
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        btn.clicked.connect(function)
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(
            QSize(ner_annotator.ICON_SIZE, ner_annotator.ICON_SIZE)
        )
        return btn

    def skip(self):
        '''
        Show the next line of the training file
        '''
        if self.current_line == len(self.input_file) - 1:
            show_dialog(
                dialog_type=QMessageBox.Warning,
                title='Warning',
                text='No more lines in the input file',
                informative='You should save the results'
            )
            return
        self.current_line += 1
        self.lines_label.setText(
            f'Line {self.current_line + 1}/{len(self.input_file)}'
        )
        self.content_text.clear()
        self.content_text.insertPlainText(self.input_file[self.current_line])
        self.output_table.setRowCount(0)
        text = self.content_text.toPlainText()
        index = self.annotation_index(text)
        if index is not None:
            for ent in self.annotations[index]['entities']:
                selection_start, selection_end, entity = ent[0], ent[1], ent[2]
                value = text[selection_start:selection_end]
                self.add_entity(entity, selection_start, selection_end, value)

    def undo(self):
        '''
        Show the previous line of the training file
        '''
        if self.current_line == 0:
            show_dialog(
                dialog_type=QMessageBox.Warning,
                title='Warning',
                text='No more previous lines in the input file',
                informative='You should save the results'
            )
            return
        self.current_line -= 1
        self.lines_label.setText(
            f'Line {self.current_line + 1}/{len(self.input_file)}'
        )
        self.content_text.clear()
        self.content_text.insertPlainText(self.input_file[self.current_line])
        self.output_table.setRowCount(0)
        text = self.content_text.toPlainText()
        index = self.annotation_index(text)
        if index is not None:
            for ent in self.annotations[index]['entities']:
                selection_start, selection_end, entity = ent[0], ent[1], ent[2]
                value = text[selection_start:selection_end]
                self.add_entity(entity, selection_start, selection_end, value)

    def record(self):
        '''
        Save the current annotations
        '''
        entities = []
        for i in range(self.output_table.rowCount()):
            ent = self.output_table.item(
                i, self.output_table_labels[ner_annotator.ENTITY_LABEL]
            ).text()
            ss = self.output_table.item(
                i,  self.output_table_labels[ner_annotator.SELECTION_START_LABEL]
            ).text()
            se = self.output_table.item(
                i,  self.output_table_labels[ner_annotator.SELECTION_END_LABEL]
            ).text()
            if ent and ss.isdigit() and se.isdigit():
                entities.append([int(ss), int(se), ent])
        annotation = {
            'content': self.content_text.toPlainText(),
            'entities': entities
        }
        index = self.annotation_index(annotation['content'])
        if index is None and entities:
            self.annotations.append(annotation)
        elif index is not None:
            if not entities:
                del self.annotations[index]
            else:
                self.annotations[index]['entities'] = entities

    def annotation_index(self, content):
        '''
        Check if the given annotation exists.
        If it does, return its index in the annotations,
        otherwise return None.
        '''
        for i, ann in enumerate(self.annotations):
            if ann['content'] == content:
                return i
        return None

    def next(self):
        '''
        Save the current annotations and go to the next line
        '''
        self.record()
        self.skip()

    def prev(self):
        '''
        Save the current annotations and go to the previous line
        '''
        self.record()
        self.undo()

    def save(self):
        '''
        Save annotations to the output file
        '''
        if self.latest_save != self.annotations:
            try:
                open(self.output_file, 'w').write(json.dumps(self.annotations))
                self.latest_save = copy.deepcopy(self.annotations)
                show_dialog(
                    dialog_type=QMessageBox.Information,
                    title='Success',
                    text='The output file was successfully saved'
                )
            except Exception as err:
                show_dialog(
                    dialog_type=QMessageBox.Critical,
                    title='Error',
                    text='An error occurred while saving the output file',
                    informative=str(err)
                )
        else:
            show_dialog(
                dialog_type=QMessageBox.Information,
                title='No data to save',
                text='You do not have new data to save'
            )

    def classify(self):
        '''
        Classify the current text using the given model
        '''
        entities = self.model.classify(self.content_text.toPlainText())
        for ent in entities:
            if ent['label'] in self.entities:
                self.add_entity(
                    ent['label'], ent['start'], ent['end'], ent['text']
                )

    def stop(self):
        '''
        Complete the annotating process
        '''
        self.record()
        self.save()

    def add_selected_entity(self, entity):
        '''
        Add the selected entity to the output table
        '''
        cursor = self.content_text.textCursor()
        value = cursor.selectedText()
        selection_start = cursor.selectionStart()
        selection_end = cursor.selectionEnd()
        self.add_entity(entity, selection_start, selection_end, value)

    def add_entity(self, entity, selection_start, selection_end, value):
        '''
        Add the given entity to the output table
        '''
        if selection_end - selection_start > 0:
            rows = self.output_table.rowCount()
            self.output_table.insertRow(rows)
            self.output_table.setItem(
                rows,
                self.output_table_labels[ner_annotator.ENTITY_LABEL],
                QTableWidgetItem(entity)
            )
            self.output_table.setItem(
                rows,
                self.output_table_labels[ner_annotator.VALUE_LABEL],
                QTableWidgetItem(value)
            )
            self.output_table.setItem(
                rows,
                self.output_table_labels[ner_annotator.SELECTION_START_LABEL],
                QTableWidgetItem(str(selection_start))
            )
            self.output_table.setItem(
                rows,
                self.output_table_labels[ner_annotator.SELECTION_END_LABEL],
                QTableWidgetItem(str(selection_end))
            )
            self.output_table.resizeRowsToContents()
            self.set_highlighting(rows, selection_start, selection_end)

    def highlight(self, selection_start, selection_end, color):
        '''
        Color selected text in the content section
        '''
        cursor = self.content_text.textCursor()
        cursor.setPosition(int(selection_start))
        cursor.setPosition(int(selection_end), QTextCursor.KeepAnchor)
        fmt = QTextCharFormat()
        if isinstance(color, str):
            fmt.setBackground(QColor("transparent"))
        elif isinstance(color, tuple) or isinstance(color, list):
            if len(color) == 3:
                fmt.setBackground(
                    QColor(color[0], color[1], color[2])
                )
            elif len(color) == 4:
                fmt.setBackground(
                    QColor(color[0], color[1], color[2], color[3])
                )
        cursor.setCharFormat(fmt)

    def set_highlighting(self, output_row, selection_start, selection_end):
        '''
        Color selected text and the corresponding row in the output table
        '''
        # Color selected text
        color = [
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            80
        ]
        self.highlight(selection_start, selection_end, color)

        # Color entire row in output table
        for output_col in self.output_table_labels.values():
            self.output_table.item(output_row, output_col).setBackground(
                QColor(color[0], color[1], color[2], 80)
            )

    def clear_highlighting(self, output_row):
        '''
        Remove highlighting from text when removing 
        corresponding entity in output table
        '''
        selection_start = self.output_table.item(
            output_row, self.output_table_labels[ner_annotator.SELECTION_START_LABEL]
        ).text()
        selection_end = self.output_table.item(
            output_row, self.output_table_labels[ner_annotator.SELECTION_END_LABEL]
        ).text()
        self.highlight(selection_start, selection_end, "transparent")

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            select = self.output_table.selectionModel()
            for index in select.selectedRows():
                self.clear_highlighting(index.row())
                self.output_table.removeRow(index.row())
        elif event.type() == QEvent.KeyPress and event.key() in range(Qt.Key_1, Qt.Key_9):
            if len(self.entities) < 10:
                index = int(event.key()) - 48
                self.add_selected_entity(self.entities[index - 1])

    def closeEvent(self, event):
        self.record()
        if self.latest_save != self.annotations:
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
