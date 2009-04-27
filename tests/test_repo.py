import unittest
import os, os.path

from cork import CorkNote, CorkRepo, open_repo

class RepoTest(unittest.TestCase):
    def write_test_file(self, filepath, data):
        folderpath = os.path.join(self._temp_dir, os.path.split(filepath)[0])
        if not os.path.isdir(folderpath):
            os.makedirs(folderpath)
        f = open(os.path.join(self._temp_dir, filepath), 'w')
        f.write(data)
        f.close()

    def setUp(self):
        from tempfile import mkdtemp
        self._temp_dir = mkdtemp()

    def tearDown(self):
        from shutil import rmtree
        rmtree(self._temp_dir)

    def test_fs_repo(self):
        self.write_test_file('n1.note', 'x: 13\n')
        self.write_test_file('f2/n2.note', 'y: 42\n')
        repo = open_repo(self._temp_dir)
        self.failUnlessEqual(repo.walk('/n1')['x'], 13)
        self.failUnlessEqual(repo.walk('/f2/n2')['y'], 42)
        self.failUnlessRaises(KeyError, lambda: repo.walk('none'))
        self.failUnlessRaises(KeyError, lambda: repo.walk('/f2/none'))

    def test_traverse(self):
        repo = CorkNote({'_children_': {
            'n1': CorkNote({'a': 1}),
            'f2': CorkNote({'a': 2, '_children_': {
                'n2': CorkNote({'a': 3}),
            }}),
        }})
        self.failUnlessEqual(repo.walk('/n1')['a'], 1)
        self.failUnlessEqual(repo.walk('/f2')['a'], 2)
        self.failUnlessEqual(repo.walk('/f2/n2')['a'], 3)
        self.failUnlessEqual(repo.walk('/f2/n2').walk('/n1')['a'], 1)
        self.failUnlessRaises(KeyError, lambda: repo.walk('none'))

if __name__ == '__main__': unittest.main()
