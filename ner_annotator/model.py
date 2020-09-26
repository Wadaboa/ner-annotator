'''
Define NER models to classify entities and convert JSON data
'''


def load_model(model_path):
    '''
    Try to load the correct NER model
    '''
    model = None
    correct_subclass = None
    for subclass in NERModel.__subclasses__():
        model = subclass._load_model(model_path)
        if model is not None:
            correct_subclass = subclass

    if correct_subclass is None:
        raise Exception(
            'Could not find the corresponding library for the given NER model'
        )
    return correct_subclass(model_path, model=model)


class NERModel(object):

    def __init__(self, model_path, model=None):
        self.model_path = model_path
        if model is not None:
            self.model = model
        else:
            self.model = self._load_model(self.model_path)

    @classmethod
    def _load_model(cls, model_path):
        '''
        Try to load the given model. If there is an error,
        it means that either the corresponding library is not installed
        or that the given model cannot be loaded by that library
        '''
        raise NotImplementedError

    def classify(self, text):
        '''
        Classify the given text and return the retrieved entities.
        Each element of the return array should be a dictionary with
        the following schema:
        {
            'label': Entity label,
            'start': Initial index of the entity inside the whole text,
            'end': Final index of the entity inside the whole text,
            'text': Labeled text
        }
        '''
        raise NotImplementedError

    def from_json(self, train_json):
        '''
        Convert JSON data to model data
        '''
        raise NotImplementedError


class SpaCyNERModel(NERModel):

    def __init__(self, model_path, model=None):
        super(SpaCyNERModel, self).__init__(model_path, model)

    @classmethod
    def _load_model(cls, model_path):
        try:
            import spacy
            return spacy.load(model_path)
        except:
            return None

    def classify(self, text):
        entities = []
        doc = self.model(text)
        for ent in doc.ents:
            entities.append({
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'text': ent.text
            })
        return entities

    def from_json(self, train_json):
        '''
        Convert JSON data to SpaCy data
        '''
        train_data = []
        for data in train_json:
            ents = [tuple(entity) for entity in data['entities']]
            train_data.append((data['content'], {'entities': ents}))
        return train_data
