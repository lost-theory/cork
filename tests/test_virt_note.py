import unittest

from cork import VirtualNote, CorkNote, CorkRepo

class InheritanceTest(unittest.TestCase):
    def test_inheritance(self):
        repo = CorkRepo()
        repo.add_vnote('/a', VirtualNote({'x': 'y'}))
        repo.add_vnote('/b', VirtualNote({'__inherit__':'/a'}))
        self.failUnlessEqual(repo['/a']['x'], 'y')
        self.failUnless('x' in repo['/b'])
        self.failUnlessEqual(repo['/b']['x'], 'y')
        self.failUnlessEqual(repo['/b'].get('x'), 'y')
        self.failUnlessRaises(KeyError, lambda: repo['/b'].get('z'))

class VirtualNoteTest(unittest.TestCase):
    def make_virt_note(self):
        def add_method(note, a, b):
            return a+b
        def get_x_method(note):
            return note['x']
        vnote = VirtualNote({
            'x': 13,
            'add': add_method,
            'get_x': get_x_method,
        })
        return vnote

    def test_vnote(self):
        vnote = self.make_virt_note()
        self.failUnless(isinstance(vnote, CorkNote))
        self.failUnlessEqual(vnote['x'], 13)
        self.failUnlessEqual(vnote.get('x'), 13)
        self.failUnlessEqual(vnote.get('y', 0), 0)
        self.failUnlessEqual(vnote['add'](1, 2), 3)
        self.failUnlessEqual(vnote['get_x'](), 13)

    def test_vnote_in_repo(self):
        vnote = self.make_virt_note()
        repo = CorkRepo()
        repo.add_vnote('/vnote', vnote)
        self.failUnless('/vnote' in repo)
        self.failUnless(repo['/vnote'] is vnote)
        self.failUnless(repo['/vnote'].repo is repo)

if __name__ == '__main__': unittest.main()
