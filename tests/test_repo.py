import unittest
import os, os.path

from cork import CorkNote, CorkRepo, open_repo

class RepoTest(unittest.TestCase):
    def filepath(self, rel_path):
        folderpath = os.path.join(self._temp_dir, os.path.split(rel_path)[0])
        if not os.path.isdir(folderpath):
            os.makedirs(folderpath)
        return os.path.join(self._temp_dir, rel_path)

    def write_test_file(self, rel_path, data):
        f = open(self.filepath(rel_path), 'w')
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

    def test_fs_repo_caching(self):
        self.write_test_file('n1.note', 'x: 13\n')
        repo = open_repo(self._temp_dir)
        n1 = repo.walk('/n1')
        self.failUnless(n1 is repo.walk('/n1'), 'No caching happens!')
        mtime = os.stat(self.filepath('n1.note')).st_mtime + 1
        os.utime(self.filepath('n1.note'), (mtime, mtime))
        self.failIf(n1 is repo.walk('/n1'), 'Cache is not refreshed!')

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

    def test_save_load(self):
        self.write_test_file('n1.note', 'x: 13\n')
        repo = open_repo(self._temp_dir)
        n1 = repo.walk('/n1')
        test_data = {'a': 'b', 'c': ['x', 'y', 'z', {'u':'v'}]}
        n1['y'] = test_data
        n1['_save_']()
        repo2 = open_repo(self._temp_dir)
        loaded_data = repo2.walk('/n1')['y']
        self.failUnlessEqual(test_data, loaded_data)

if __name__ == '__main__': unittest.main()
