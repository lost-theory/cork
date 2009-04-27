# Cork library core notes

import os
from . import CorkNote, CorkMethod, yaml

lib = {}


# _lib_/cork/web

def _web_wsgi(note, environ, start_response):
    from webob import Request
    request = Request(environ)
    response = note['_web_'](request)
    return response(environ, start_response)
lib['_lib_/cork/web'] = CorkNote({'_wsgi_': CorkMethod(_web_wsgi)})


# _lib_/cork/basenote

def _basenote_get_child(note, child_name):
    inline_kids = note.get('_children_', {})
    if child_name in inline_kids:
        return inline_kids[child_name]
base_note = CorkNote({'_get_child_': CorkMethod(_basenote_get_child), '_children_': {}})
base_note.inherit = []
lib['_lib_/cork/basenote'] = base_note


# _lib_/cork/fsnote

def _fsnote_get_child(note, child_name):
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
lib['_lib_/cork/fsnote'] = CorkNote({'_get_child_': CorkMethod(_fsnote_get_child)})
