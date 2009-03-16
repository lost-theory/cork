import yaml

class CorkNote(dict):
    def __init__(self, content, repo=None):
        self.repo = repo
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

    def __getitem__(self, key):
        if key in self:
            val = dict.get(self, key)

        elif key != '__inherit__' and '__inherit__' in self:
            superclass = self['__inherit__']
            if superclass not in self.repo:
                raise NotImplementedError # TODO

            val = self.repo[superclass][key]

        else:
            raise KeyError('CorkNote has no member named "%s"' % key)

        if isinstance(val, CorkMethod):
            val = val.bind(self)
        return val


def note_constructor(loader, node):
    value = loader.construct_mapping(node)
    return CorkNote(value)
yaml.add_constructor(u'!note', note_constructor)

class CorkMethod(object):
    def __init__(self, code, note=None):
        self.code = code
        self.note = note

    def __repr__(self):
        return '<CorkMethod at 0x%x>' % id(self)

    def __call__(self, *args, **kwargs):
        return self.code['__call__'](self.note, *args, **kwargs)

    def bind(self, note):
        return CorkMethod(self.code, note)

class CorkRepo(object):
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def __repr__(self):
        return '<CorkRepo at "%s">' % self.repo_dir.encode('ascii', 'replace')

    def _get_note_list(self):
        import os
        notes = set()
        #for dirpath, dirnames, filenames in os.walk(self.repo_dir):
        #    dirpath = dirpath[len(self.repo_dir):]
        #    notes.update(dirpath + filename for filename in filenames)
        for filename in os.listdir(self.repo_dir):
            if filename.endswith('.note'):
                notes.add('/%s' % filename[:-5])
        return notes

    def list_notes(self):
        return self._get_note_list()

    def __len__(self):
        return len(self._get_note_list())

    def __getitem__(self, key):
        # TODO: unsafe!
        raw_data = open('%s%s.note' % (self.repo_dir, key), 'rb').read()
        return CorkNote(yaml.load(raw_data), repo=self)

    def __contains__(self, key):
        return key in self._get_note_list()

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

def open_repo(repo_dir):
    return CorkRepo(repo_dir)
