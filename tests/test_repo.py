import unittest
import os, os.path

from cork import CorkNote, CorkRepo, open_repo

class FilesystemTest(object):
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

class FsRepoTest(FilesystemTest, unittest.TestCase):
    def test_fs_repo(self):
        self.write_test_file('n1.note', 'x: 13\n')
        self.write_test_file('f2/n2.note', 'y: 42\n')
        repo = open_repo(self._temp_dir)
        self.failUnless('/n1' in repo)
        self.failUnless('/f2/n2' in repo)
        self.failIf('/n0' in repo)
        self.failUnlessEqual(repo['/n1']['x'], 13)
        self.failUnlessEqual(repo['/f2/n2']['y'], 42)
        self.failUnlessRaises(KeyError, lambda: repo['none'])
        self.failUnlessRaises(KeyError, lambda: repo['/f2/none'])

class DictRepoTest(unittest.TestCase):
    def test_dict_repo(self):
        n1_note = CorkNote({'x': 13})
        data_dict = {'n1': n1_note}
        repo = CorkRepo(data_dict)
        self.failUnless('/n1' in repo)
        self.failIf('/n0' in repo)
        self.failUnlessEqual(repo['/n1']['x'], 13)

    def test_traverse(self):
        n1_note = CorkNote({'a': 1})
        n2_note = CorkNote({'b': 2})
        repo = CorkRepo({
            'n1': n1_note,
            'f2': CorkRepo({
                'n2': n2_note,
            })
        })
        self.failUnless(repo.traverse('/n1') is n1_note)
        self.failUnless(repo.traverse('/f2/n2') is n2_note)
        self.failUnless(repo.traverse('none') is None)

if __name__ == '__main__': unittest.main()
