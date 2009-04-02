import yaml

class CorkLookupError(KeyError):
    pass

class CorkNote(dict):
    def __init__(self, content, repo=None):
        self.repo = repo
        self.update(content)
        # TODO: keyorder is not tested
        if isinstance(content, list):
            self.keyorder = [key for key, value in content]
        else:
            self.keyorder = None
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

    def iteritems(self):
        if self.keyorder is None:
            return dict.iteritems(self)
        else:
            return [(key, self[key]) for key in self.keyorder]

    def __repr__(self):
        return '<CorkNote at 0x%x>' % id(self)

    def _lookup(self, key):
        if dict.__contains__(self, key):
            return dict.get(self, key)

        elif key != '_inherit_' and dict.__contains__(self, '_inherit_'):
            superclass = self['_inherit_']
            if superclass not in self.repo:
                raise NotImplementedError # TODO

            return self.repo[superclass][key]

        else:
            raise CorkLookupError

    def __contains__(self, key):
        try:
            self._lookup(key)
            return True
        except CorkLookupError:
            return False

    def get(self, key, default=CorkLookupError):
        try:
            val = self._lookup(key)
        except CorkLookupError:
            if default is CorkLookupError:
                raise KeyError('CorkNote has no member named "%s"' % key)
            else:
                return default

        if isinstance(val, CorkMethod):
            val = val.bind(self)

        return val

    def __getitem__(self, key):
        try:
            val = self._lookup(key)
        except CorkLookupError:
            raise KeyError('CorkNote has no member named "%s"' % key)

        if isinstance(val, CorkMethod):
            val = val.bind(self)

        return val

class VirtualNote(CorkNote):
    def __init__(self, contents):
        for name in contents:
            if callable(contents[name]):
                contents[name] = CorkMethod(contents[name])
        super(VirtualNote, self).__init__(contents)

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
        return self.code(self.note, *args, **kwargs)

    def bind(self, note):
        return CorkMethod(self.code, note)

class CorkRepo(object):
    def __init__(self, repo_dir=None):
        self.repo_dir = repo_dir
        self.virt_notes = {}

    def add_vnote(self, path, note):
        self.virt_notes[path] = note
        note.repo = self

    def __repr__(self):
        if self.repo_dir is None:
            return '<CorkRepo with no dir>'
        return '<CorkRepo at "%s">' % self.repo_dir.encode('ascii', 'replace')

    def _get_note_list(self, include_virtual=False):
        import os
        notes = set()
        if include_virtual:
            notes.update(self.virt_notes.iterkeys())
        #for dirpath, dirnames, filenames in os.walk(self.repo_dir):
        #    dirpath = dirpath[len(self.repo_dir):]
        #    notes.update(dirpath + filename for filename in filenames)
        if self.repo_dir is not None:
            for filename in os.listdir(self.repo_dir):
                if filename.endswith('.note'):
                    notes.add('/%s' % filename[:-5])
        return notes

    def list_notes(self):
        return self._get_note_list()

    def __len__(self):
        return len(self._get_note_list())

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=KeyError):
        if key in self.virt_notes:
            return self.virt_notes[key]

        # TODO: unsafe!
        try:
            raw_data = open('%s%s.note' % (self.repo_dir, key), 'rb').read()
        except IOError:
            if default is KeyError:
                raise KeyError('Note "%s" not found in repository "%s"' %
                        (key, self.repo_dir))
            else:
                return default
        return CorkNote(yaml.load(raw_data), repo=self)

    def __contains__(self, key):
        return key in self._get_note_list(include_virtual=True)

    def wsgi(self, env, start_response):
        path = env['PATH_INFO']
        note = self.get(path, None)
        if note is None:
            start_response("404 Not Found", [('Content-Type', 'text/plain')])
            return [path]
        elif isinstance(note.get('_wsgi_', None), CorkMethod):
            return note['_wsgi_'](env, start_response)
        else:
            start_response("200 OK", [('Content-Type', 'text/plain')])
            return [yaml.dump(dict(note))]

def method_constructor(loader, node):
    code = loader.construct_scalar(node)
    filename = '<CorkMethod code>'
    c = compile(code, filename, 'exec')
    d = {}
    eval(c, d)
    return CorkMethod(d['__call__'])
yaml.add_constructor(u'!py', method_constructor)

def parse_note(raw_data):
    return CorkNote(yaml.load(raw_data))

def open_repo(repo_dir):
    return CorkRepo(repo_dir)
