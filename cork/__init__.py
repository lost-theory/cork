import os
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

def _make_vnote_web():
    def wsgi_method(note, environ, start_response):
        from webob import Request
        request = Request(environ)
        response = note['_web_'](request)
        return response(environ, start_response)
    return VirtualNote({'_wsgi_': wsgi_method})

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

class FsNoteResolver(object):
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir

    def get(self, key, default):
        # TODO: unsafe!
        path = os.path.join(self.repo_dir, key)
        if os.path.isdir(path):
            return open_repo(path)
        try:
            raw_data = open('%s.note' % path, 'rb').read()
        except IOError:
            return default
        return CorkNote(yaml.load(raw_data))

    def keys(self):
        notes = []
        for filename in os.listdir(self.repo_dir):
            if filename.endswith('.note'):
                notes.append('%s' % filename[:-5])
        return notes

class CorkRepo(object):
    def __init__(self, notes_dict):
        self.notes_dict = notes_dict
        self.virt_notes = {}
        self.add_vnote('_lib_/cork/web', _make_vnote_web())
        self.parent_repo = None

    def add_vnote(self, path, note):
        self.virt_notes[path] = note
        note.repo = self

    def __repr__(self):
        if isinstance(self.notes_dict, FsNoteResolver):
            return '<CorkRepo at "%s">' % self.notes_dict.repo_dir.encode('ascii', 'replace')
        return '<CorkRepo with no dir>'

    def _get_note_list(self, include_virtual=False):
        notes = set()
        if include_virtual:
            notes.update(self.virt_notes.iterkeys())
        notes.update(self.notes_dict.keys())
        return notes

    def list_notes(self):
        return self._get_note_list()

    def __len__(self):
        return len(self._get_note_list())

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, default=KeyError):
        note = self.traverse(key)
        if note is not None:
            return note
        if default is KeyError:
            # TODO: test this error
            raise KeyError('Note "%s" not found in repository' % key)
        else:
            return default

    def traverse(self, note_ref):
        if note_ref.startswith('/'):
            repo = self
            while repo.parent_repo is not None:
                repo = repo.parent_repo
            return repo.traverse(note_ref[1:])

        if note_ref in self.virt_notes:
            value = self.virt_notes[note_ref]
            value.repo = self
            return value

        if '/' in note_ref:
            note_ref, sub_note_ref = note_ref.split('/', 1)
        else:
            sub_note_ref = None

        value = self.notes_dict.get(note_ref, None)

        if isinstance(value, CorkRepo):
            if sub_note_ref == '':
                sub_note_ref = '_index_'
            value.parent_repo = self # TODO: set parent_repo on repo creation
            return value.traverse(sub_note_ref)

        if isinstance(value, CorkNote):
            # TODO: set parent repo on note creation
            value.repo = self

        return value

    def __contains__(self, key):
        return self.traverse(key) is not None

    def wsgi(self, env, start_response):
        path = env['PATH_INFO']
        note = self.get(path, None)
        if note is None:
            start_response("404 Not Found", [('Content-Type', 'text/plain')])
            return ['Not found: ', path]
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
    return CorkRepo(FsNoteResolver(repo_dir))
