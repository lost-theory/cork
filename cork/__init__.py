import yaml

class CorkNote(dict):
    def __init__(self, content):
        self.update(content)
        def walk(obj):
            if isinstance(obj, CorkMethod):
                obj.note = self
            elif isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, (list, tuple, set)):
                for v in obj:
                    walk(v)
        walk(self)

    def __repr__(self):
        return '<CorkNote at 0x%x>' % id(self)

def note_constructor(loader, node):
    value = loader.construct_mapping(node)
    return CorkNote(value)
yaml.add_constructor(u'!note', note_constructor)

class CorkMethod(object):
    def __init__(self, code):
        self.code = code

    def __repr__(self):
        return '<CorkMethod at 0x%x>' % id(self)

    def __call__(self, *args, **kwargs):
        return self.code['__call__'](self.note, *args, **kwargs)

def method_constructor(loader, node):
    code = loader.construct_scalar(node)
    filename = '<CorkMethod code>'
    c = compile(code, filename, 'exec')
    d = {}
    eval(c, d)
    return CorkMethod(d)
yaml.add_constructor(u'!py', method_constructor)

def parse_note(raw_data):
    return CorkNote(yaml.load(raw_data))
