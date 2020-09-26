'''
NER annotator entry point
'''


import sys
import os
import argparse
import json

from PyQt5.QtWidgets import QApplication

import ner_annotator


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
            f'Please enter a file with one of the following formats: {valid_fmts}'
        )

    return True


def find_config_entities(config_json, config_model):
    '''
    Return the config model entities, given the config json
    and the config model name
    '''
    models = config_json['models']
    for model in models:
        if model['name'] == config_model:
            return model['entities']
    return None


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
        '-e', '--entities', dest='entities', action='store', nargs='+',
        type=str, help='list of entities to be classified'
    )
    parser.add_argument(
        '-m', '--model', dest='model', action='store',
        type=str, help='path to an existing NER model'
    )
    parser.add_argument(
        '-o', '--output', dest='output', action='store',
        type=str, help='path to the output file'
    )
    parser.add_argument(
        '-c', '--config', dest='config', action='store',
        type=str, help='path to the config file'
    )
    parser.add_argument(
        '-n', '--config-model', dest='config_model', action='store',
        type=str, help='name of the model to load from the config file'
    )
    return parser


def main():
    parser = parse_args()
    args = parser.parse_args()

    if is_file_valid(args.input, ner_annotator.VALID_IN_FMT):
        input_file = open(args.input, 'r').read().splitlines()
        if args.output is None:
            args.output = (
                os.path.abspath(os.path.join(
                    os.path.dirname(args.input), 'output.json'
                ))
            )
        elif not is_file_valid(args.output, ner_annotator.VALID_OUT_FMT):
            raise Exception(
                f'The output file has an invalid extension: choose between {ner_annotator.VALID_OUT_FMT}'
            )
        if args.model is not None and not os.path.exists(args.model):
            raise Exception(
                'The given NER model does not exist'
            )
        entities = args.entities
        if args.config is not None:
            if not os.path.exists(args.config):
                raise Exception(
                    'The given config file does not exist'
                )
            if args.config_model is None:
                raise Exception(
                    'You have to enter the name of the config model to use'
                )
            with open(args.config, 'r') as f:
                data = f.read()
            config_json = json.loads(data)
            entities = find_config_entities(config_json, args.config_model)
            if entities is None:
                raise Exception(
                    'The config model name you entered is not valid'
                )
        if entities is None:
            raise Exception(
                'You have to insert entities manually or use a config file'
            )

        QApplication.setStyle("fusion")
        app = QApplication(sys.argv)
        app.setStyleSheet(ner_annotator.STYLE)
        window = ner_annotator.NERAnnotator(
            input_file, args.output, entities, args.model
        )
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
