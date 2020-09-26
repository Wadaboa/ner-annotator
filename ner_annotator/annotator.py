'''
Define the main window
'''


import json
import copy
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
    QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QEvent, QSize
from PyQt5.QtGui import QIcon
import spacy

import ner_annotator


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

    def __init__(self, input_file, output_file, entities, model=None):
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
            spacy.load(model) if model is not None
            else None
        )
        self.annotations = []
        self.current_line = 0
        self.latest_save = []

        # Main layout
        self.central_widget = QWidget(self)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.left_widget = QWidget(self.central_widget)
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_bottom_widget = QWidget(self.left_widget)
        self.left_bottom_layout = QHBoxLayout(self.left_bottom_widget)
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
        self.lines_label = QLabel(self.left_widget)
        self.lines_label.setText(f'Line 1/{len(self.input_file)}')
        self.output_label = QLabel(self.left_widget)
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
            0, len(self.output_table_labels), self.left_widget
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
            self.output_table_labels[ner_annotator.SELECTION_START_LABEL], QHeaderView.ResizeToContents
        )
        self.output_table.horizontalHeader().setSectionResizeMode(
            self.output_table_labels[ner_annotator.SELECTION_END_LABEL], QHeaderView.ResizeToContents
        )
        self.left_layout.addWidget(self.content_label, 0, Qt.AlignCenter)
        self.left_layout.addWidget(self.content_text)
        self.left_layout.addWidget(self.lines_label, 0, Qt.AlignRight)
        self.left_layout.addWidget(self.output_label, 0, Qt.AlignCenter)
        self.left_layout.addWidget(self.output_table)

        # Left bottom layout
        self.prev_button = self.set_button(
            icon_path=ner_annotator.PREV_ICON_PATH,
            function=self.prev,
            parent=self.left_bottom_widget
        )
        if self.model is not None:
            self.classify_button = self.set_button(
                icon_path=ner_annotator.CLASSIFY_ICON_PATH,
                function=self.classify,
                parent=self.left_bottom_widget
            )
        self.next_button = self.set_button(
            icon_path=ner_annotator.NEXT_ICON_PATH,
            function=self.next,
            parent=self.left_bottom_widget
        )
        self.skip_button = self.set_button(
            icon_path=ner_annotator.SKIP_ICON_PATH,
            function=self.skip,
            parent=self.left_bottom_widget
        )
        self.save_button = self.set_button(
            icon_path=ner_annotator.SAVE_ICON_PATH,
            function=self.stop,
            parent=self.left_bottom_widget
        )
        self.left_bottom_layout.addWidget(self.prev_button)
        if self.model is not None:
            self.left_bottom_layout.addWidget(self.classify_button)
        self.left_bottom_layout.addWidget(self.next_button)
        self.left_bottom_layout.addWidget(self.skip_button)
        self.left_bottom_layout.addWidget(self.save_button)
        self.left_layout.addWidget(self.left_bottom_widget)

        # Right layout
        self.entities_label = QLabel(self.right_widget)
        self.entities_label.setText('Entities')
        self.entities_label.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )
        self.right_layout.addWidget(self.entities_label, 0, Qt.AlignCenter)
        self.entities_buttons = {}
        for i, entity in enumerate(self.entities):
            text = entity
            if len(self.entities) < 10:
                text = f'{i + 1}. ' + text
            self.entities_buttons[entity] = QPushButton(
                text, self.right_widget
            )
            self.entities_buttons[entity].setSizePolicy(
                QSizePolicy.Expanding, QSizePolicy.Expanding
            )
            self.entities_buttons[entity].clicked.connect(
                partial(self.add_selected_entity, entity)
            )
            self.right_layout.addWidget(self.entities_buttons[entity])

        # Main layout
        self.main_layout.addWidget(self.left_widget)
        self.main_layout.addWidget(self.right_widget)
        self.setCentralWidget(self.central_widget)

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
        doc = self.model(self.content_text.toPlainText())
        for ent in doc.ents:
            if ent.label_ in self.entities:
                self.add_entity(
                    ent.label_, ent.start_char, ent.end_char, ent.text
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

    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            select = self.output_table.selectionModel()
            for index in select.selectedRows():
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
