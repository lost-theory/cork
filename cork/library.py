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
    if not hasattr(note, '_fsnote_child_cache'):
        note._fsnote_child_cache = {}

    child_paths = [
         child_location + '.note',
         child_location + '/_index_.note',
    ]
    for child_path in child_paths:
        if os.path.isfile(child_path):
            if os.path.isfile(child_path):
                # TODO: work with filehandles from this point on; should be safer
                child = note._fsnote_child_cache.get(child_path, None)
                mtime = os.stat(child_path).st_mtime
                if child is not None and mtime == child._fsnote_mtime:
                    return child
                f = open(child_path)
                raw_data = f.read()
                f.close()
                content = yaml.load(raw_data)
                break
    else:
        if not os.path.isdir(child_location):
            return None
        child_path = child_location
        mtime = os.stat(child_path).st_mtime
        content = {}

    child = CorkNote(content, inherit=['_lib_/cork/fsnote'],
        parent_note=note, location=child_location)
    child._fsnote_mtime = mtime
    note._fsnote_child_cache[child_path] = child
    return child
lib['_lib_/cork/fsnote'] = CorkNote({'_get_child_': CorkMethod(_fsnote_get_child)})
