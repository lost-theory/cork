import os
import yaml

class CorkLookupError(KeyError): pass

class CorkNote(dict):
    def __init__(self, content={}, inherit=[], location=None, parent_note=None):
        self.inherit = inherit + ['_lib_/cork/basenote']
        self.location = location
        self.parent_note = parent_note
        self.update(content)
        self.lookup_cache = {}

        if isinstance(content, list):
            keyorder = []
        else:
            keyorder = None
            content = content.iteritems()

        for key, value in content:
            if key == '_children_':
                for child_name in value:
                    if not isinstance(value[child_name], CorkNote):
                        value[child_name] = CorkNote(value[child_name])
                    value[child_name].parent_note = self

            elif isinstance(value, CorkMethod):
                value.note = self

            self[key] = value

            if keyorder is not None:
                keyorder.append(key)

        self.keyorder = keyorder

    def iteritems(self):
        for key in self.iterkeys():
            yield (key, self[key])

    def items(self):
        return list(self.iteritems())

    def iterkeys(self):
        if self.keyorder is not None:
            return self.keyorder.__iter__()
        return dict.iterkeys(self)

    def keys(self):
        return list(self.iterkeys())

    def __repr__(self):
        return '<CorkNote at 0x%x>' % id(self)

    def _lookup(self, key):
        if dict.__contains__(self, key):
            return dict.get(self, key)

        elif key in self.lookup_cache:
            value = self.lookup_cache[key]
            if value is None:
                pass # we found a lookup loop
            else:
                return value

        elif key != '_inherit_':
            explicit_inherit = dict.get(self, '_inherit_', None)
            if explicit_inherit:
                explicit_inherit = [explicit_inherit]
            else:
                explicit_inherit = []
            mro = explicit_inherit + self.inherit
            for superclass in mro:
                try:
                    self.lookup_cache[key] = None # set a flag to catch loops
                    value = self.walk(superclass)[key]
                    self.lookup_cache[key] = value
                    return value
                except (KeyError, CorkLookupError), e:
                    pass

        raise CorkLookupError(key)

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
        return self.get(key)

    def walk(self, note_ref):
        from library import lib
        if note_ref in lib:
            return lib[note_ref]

        if note_ref.startswith('/'):
            root = self
            while root.parent_note is not None:
                root = root.parent_note
            return root.walk(note_ref[1:])

        if '/' in note_ref:
            note_ref, sub_note_ref = note_ref.split('/', 1)
        else:
            sub_note_ref = None

        if note_ref == '..':
            parent = self.parent_note
            if parent is None:
                parent = self
            if sub_note_ref is None:
                return parent
            else:
                return parent.walk(sub_note_ref)

        value = self['_get_child_'](note_ref)
        if value is None:
            raise KeyError

        if sub_note_ref is None:
            return value
        else:
            return value.walk(sub_note_ref)

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
    def __init__(self, root_note):
        self.root_note = root_note

    def __repr__(self):
        return '<CorkRepo at "%s">' % self.root_note.location

    def walk(self, path):
        return self.root_note.walk(path)

    def wsgi(self, env, start_response):
        path = env['PATH_INFO']
        try:
            note = self.walk(path)
        except KeyError:
            note = None

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

def note_constructor(loader, node):
    value = loader.construct_mapping(node)
    return CorkNote(value)
yaml.add_constructor(u'!note', note_constructor)

def parse_note(raw_data):
    return CorkNote(content=yaml.load(raw_data))

def open_repo(repo_dir):
    if repo_dir.endswith('/'):
        repo_dir = repo_dir[:-1]
    root_note = CorkNote(location=repo_dir, inherit=['_lib_/cork/fsnote'])
    return CorkRepo(root_note)
