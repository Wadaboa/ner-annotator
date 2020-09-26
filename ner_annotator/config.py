'''
Store configuration values
'''


from pkg_resources import resource_filename
from os.path import abspath

from PyQt5.QtCore import QFile


# Input/output formats
VALID_IN_FMT = ('.txt')
VALID_OUT_FMT = ('.json')

# Output table labels
ENTITY_LABEL = 'Entity'
VALUE_LABEL = 'Value'
SELECTION_START_LABEL = 'Start'
SELECTION_END_LABEL = 'End'

# CSS
STYLE = ""
STYLE_FILE_PATH = abspath(resource_filename(
    'ner_annotator.resources.style', 'style.qss'
))
STYLE_FILE = QFile(STYLE_FILE_PATH)
if STYLE_FILE.open(QFile.ReadOnly):
    STYLE = STYLE_FILE.readAll().data().decode()

# Icons
NEXT_ICON_PATH = abspath(resource_filename(
    'ner_annotator.resources.icons', 'next.png'
))
PREV_ICON_PATH = abspath(resource_filename(
    'ner_annotator.resources.icons', 'previous.png'
))
SKIP_ICON_PATH = abspath(resource_filename(
    'ner_annotator.resources.icons', 'skip.png'
))
SAVE_ICON_PATH = abspath(resource_filename(
    'ner_annotator.resources.icons', 'save.png'
))
CLASSIFY_ICON_PATH = abspath(resource_filename(
    'ner_annotator.resources.icons', 'categorize.png'
))
ICON_SIZE = 64

# Main window
WINDOW_TITLE = "NER Annotator"
