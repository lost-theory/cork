import yaml

class CorkNote(dict):
    def __init__(self, content):
        self.update(content)
    def __repr__(self):
        return '<CorkNote object at 0x%x>' % id(self)

def note_constructor(loader, node):
    value = loader.construct_mapping(node)
    return CorkNote(value)
yaml.add_constructor(u'!note', note_constructor)

def parse_note(raw_data):
    return CorkNote(yaml.load(raw_data))
