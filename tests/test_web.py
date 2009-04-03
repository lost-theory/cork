import unittest
from wsgiref.validate import validator
from wsgiref.util import setup_testing_defaults
from cStringIO import StringIO

from cork import VirtualNote, CorkRepo

def wsgi_test(app, path='/', query_string=''):
    env = {'PATH_INFO': path, 'SCRIPT_NAME': '', 'QUERY_STRING': query_string}
    setup_testing_defaults(env)
    output = {}
    def start_response(status, headers, exc_info=None):
        output.update(status=status, headers=headers, exc_info=exc_info)
    body = validator(app)(env, start_response)
    output['body'] = ''.join(body)
    body.close()
    return output

class VirtualNoteTest(unittest.TestCase):
    def make_vnote(self):
        def wsgi_method(note, environ, start_response):
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return ['Hello world!', environ['QUERY_STRING']]
        vnote = VirtualNote({'_wsgi_': wsgi_method})
        return vnote

    def make_web_vnote(self):
        def web_method(note, req):
            from webob import Response
            action = req.GET['action']
            if action == '404':
                return Response(status=404)
            elif action == 'ping':
                return Response('pong')
        web_vnote = VirtualNote({
            '_inherit_': '_lib_/cork/web',
            '_web_': web_method,
        })
        return web_vnote

    def make_repo(self, notes):
        repo = CorkRepo({})
        for name, note in notes.iteritems():
            repo.add_vnote(name, note)
        return repo

    def test_wsgi(self):
        vnote = self.make_vnote()
        output = wsgi_test(vnote['_wsgi_'], query_string='a=b')
        self.failUnlessEqual(output['status'], '200 OK')
        self.failUnlessEqual(output['body'], 'Hello world!a=b')

    def test_wsgi_in_repo(self):
        repo = self.make_repo({'/vnote':self.make_vnote()})
        self.failUnlessEqual(wsgi_test(repo.wsgi, '/nope')['status'], '404 Not Found')
        output = wsgi_test(repo.wsgi, '/vnote')
        self.failUnlessEqual(output['status'], '200 OK')
        self.failUnlessEqual(output['body'], 'Hello world!')

    def test_web(self):
        repo = self.make_repo({'/vnote':self.make_vnote(),
            '/web_vnote': self.make_web_vnote()})

        output = wsgi_test(repo.wsgi, '/web_vnote', 'action=404')
        self.failUnlessEqual(output['status'], '404 Not Found')

        output = wsgi_test(repo.wsgi, '/web_vnote', 'action=ping')
        self.failUnlessEqual(output['status'], '200 OK')
        self.failUnlessEqual(output['body'], 'pong')

if __name__ == '__main__': unittest.main()
