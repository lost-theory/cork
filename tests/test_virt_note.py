import unittest

from cork import CorkNote, CorkMethod

class InheritanceTest(unittest.TestCase):
    def test_inheritance(self):
        repo = CorkNote({'_children_': {
            'a': CorkNote({'x': 'y'}),
            'b': CorkNote({'_inherit_':'/a'}),
        }})
        self.failUnlessEqual(repo.walk('/a')['x'], 'y')
        self.failUnless('x' in repo.walk('/b'))
        self.failUnlessEqual(repo.walk('/b')['x'], 'y')
        self.failUnlessEqual(repo.walk('/b').get('x'), 'y')
        self.failUnlessRaises(KeyError, lambda: repo.walk('/b').get('z'))

class VirtualNoteTest(unittest.TestCase):
    def setUp(self):
        self.vnote = CorkNote({
            'x': 13,
            'add': CorkMethod(lambda note, a, b: a+b),
            'get_x': CorkMethod(lambda note: note['x']),
        })
        self.repo = CorkNote({'_children_': {
            'vnote': self.vnote,
        }})

    def test_vnote(self):
        self.failUnless(isinstance(self.vnote, CorkNote))
        self.failUnlessEqual(self.vnote['x'], 13)
        self.failUnlessEqual(self.vnote.get('x'), 13)
        self.failUnlessEqual(self.vnote.get('y', 0), 0)
        self.failUnlessEqual(self.vnote['add'](1, 2), 3)
        self.failUnlessEqual(self.vnote['get_x'](), 13)

    def test_vnote_in_repo(self):
        self.failUnless(self.repo.walk('/vnote'))
        self.failUnless(self.repo.walk('/vnote') is self.vnote)

if __name__ == '__main__': unittest.main()
