import unittest
import doctest
from os.path import normpath, dirname, join

suite = unittest.TestSuite()
for fname in ['note_format.txt', 'repository.txt']:
    doc_file = normpath(join(dirname(__file__), '../docs/%s' % fname))
    text = open(doc_file, 'rb').read().decode('utf-8')
    doc_test = doctest.DocTestParser().get_doctest(text, {}, fname, fname, 0)
    suite.addTest(doctest.DocTestCase(doc_test, optionflags=doctest.ELLIPSIS))

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite)
