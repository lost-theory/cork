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

    def test_inheritance_loop(self):
        repo = CorkNote({'_children_': {
            'a': CorkNote({'_inherit_':'/a/b', '_children_': {
                'b': CorkNote({'x': 'y'}),
            }}),
        }})
        try:
            self.failUnlessEqual(repo.walk('/a')['x'], 'y')
        except RuntimeError, e:
            self.fail('Should not raise exception - "%s"' % e)

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

    def test_keyorder(self):
        note = CorkNote([
            ('a', ''),
            ('b', ''),
            ('c', ''),
            ('d', ''),
        ])

        order = ['a', 'b', 'c', 'd']
        self.failUnlessEqual(note.keyorder, order)
        self.failUnlessEqual(list(k for k,v in note.iteritems()), order)
        self.failUnlessEqual(list(k for k,v in note.items()), order)
        self.failUnlessEqual(list(note.iterkeys()), order)
        self.failUnlessEqual(list(note.keys()), order)

if __name__ == '__main__': unittest.main()
