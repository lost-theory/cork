import unittest
from os import path

from cork import CorkNote, CorkRepo, make_cork_dict_repo, open_repo

class FilesystemTest(object):
    def write_test_file(self, filename, data):
        f = open(path.join(self._temp_dir, filename), 'w')
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
        repo = open_repo(self._temp_dir)
        self.failUnless('/n1' in repo)
        self.failUnlessEqual(repo['/n1']['x'], 13)

class DictRepoTest(unittest.TestCase):
    def test_dict_repo(self):
        n1_note = CorkNote({'x': 13})
        data_dict = {'/n1': n1_note}
        repo = make_cork_dict_repo(data_dict)
        self.failUnless('/n1' in repo)
        self.failUnlessEqual(repo['/n1']['x'], 13)

    def test_traverse(self):
        n1_note = CorkNote({})
        repo = make_cork_dict_repo({
            '/n1': n1_note,
        })
        self.failUnless(repo.traverse('/n1') is n1_note)
