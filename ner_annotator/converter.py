'''
Convert JSON formatted data to specific NER engines schemas
'''


def from_json_to_spacy(train_json):
    '''
    Convert JSON data to SpaCy data
    '''
    train_data = []
    for data in train_json:
        ents = [tuple(entity) for entity in data['entities']]
        train_data.append((data['content'], {'entities': ents}))
