import os
import yaml

class CorkLookupError(KeyError):
    pass

class CorkNote(dict):
    def __init__(self, content={}, inherit=[], location=None, parent_note=None):
        self.inherit = inherit + ['_lib_/cork/basenote']
        self.location = location
        self.parent_note = parent_note
        self.update(content)
        # TODO: keyorder is not tested

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

            if keyorder:
                keyorder.append(key)

        self.keyorder = keyorder

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

        elif key != '_inherit_':
            explicit_inherit = dict.get(self, '_inherit_', None)
            if explicit_inherit:
                explicit_inherit = [explicit_inherit]
            else:
                explicit_inherit = []
            mro = explicit_inherit + self.inherit
            for superclass in mro:
                try:
                    return self.walk(superclass)[key]
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
        try:
            val = self._lookup(key)
        except CorkLookupError:
            raise KeyError('CorkNote has no member named "%s"' % key)

        if isinstance(val, CorkMethod):
            val = val.bind(self)

        return val

    def walk(self, note_ref):
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

        value = self['_get_child_'](note_ref)
        if value is None:
            raise KeyError

        if sub_note_ref is None:
            return value
        else:
            return value.walk(sub_note_ref)

def _make_vnote_basenote():
    def get_child_method(note, child_name):
        inline_kids = note.get('_children_', {})
        if child_name in inline_kids:
            return inline_kids[child_name]
    base_note = VirtualNote({'_get_child_': get_child_method, '_children_': {}})
    base_note.inherit = []
    return base_note

def _make_vnote_fsnote():
    def get_child_method(note, child_name):
        inline_kids = note.get('_children_', {})
        if child_name in inline_kids:
            return inline_kids[child_name]
        child_location = '%s/%s' % (note.location, child_name)
        child_paths = [
             child_location + '.note',
             child_location + '/_index_.note',
        ]
        for child_path in child_paths:
            if os.path.isfile(child_path):
                if os.path.isfile(child_path):
                    f = open(child_path)
                    raw_data = f.read()
                    f.close()
                    return CorkNote(yaml.load(raw_data),
                        inherit=['_lib_/cork/fsnote'],
                        parent_note=note,
                        location=child_location)
        if os.path.isdir(child_location):
            return CorkNote(
                inherit=['_lib_/cork/fsnote'],
                parent_note=note,
                location=child_location)
    return VirtualNote({'_get_child_': get_child_method})

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

def method_constructor(loader, node):
    code = loader.construct_scalar(node)
    filename = '<CorkMethod code>'
    c = compile(code, filename, 'exec')
    d = {}
    eval(c, d)
    return CorkMethod(d['__call__'])
yaml.add_constructor(u'!py', method_constructor)

def parse_note(raw_data):
    return CorkNote(content=yaml.load(raw_data))

def open_repo(repo_dir):
    if repo_dir.endswith('/'):
        repo_dir = repo_dir[:-1]
    root_note = CorkNote(location=repo_dir, inherit=['_lib_/cork/fsnote'])
    return CorkRepo(root_note)

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

lib = {
    '_lib_/cork/basenote': _make_vnote_basenote(),
    '_lib_/cork/fsnote': _make_vnote_fsnote(),
    '_lib_/cork/web': _make_vnote_web(),
}
