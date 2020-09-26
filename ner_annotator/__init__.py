'''
NER annotator package initialization
'''


from .config import *
from .annotator import NERAnnotator
from .model import load_model


__version__ = '0.1.1'
