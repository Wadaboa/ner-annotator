'''
NER annotator package setup
'''

import sys
from setuptools import setup, find_packages

from ner_annotator import __version__


with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = fh.read().splitlines()


setup(
    name='ner_annotator',
    version=__version__,
    description='GUI useful to manually annotate text for Named Entity Recognition purposes',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/Wadaboa/ner-annotator',
    author='Alessio Falai',
    author_email='falai.alessio@gmail.com',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    keywords='ner annotator entity recognition spacy',
    packages=find_packages(),
    package_data={
        'ner_annotator.resources.icons': ['*.png'],
        'ner_annotator.resources.style': ['*.css', '*.qss']
    },
    entry_points={
        'console_scripts': [
            'ner_annotator = ner_annotator.__main__:main'
        ]
    },
    python_requires='>=3.6',
    install_requires=install_requires
)
