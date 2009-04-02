import unittest
import doctest
from os.path import normpath, dirname, join

def doctest_to_unittest(fname):
    doc_file = normpath(join(dirname(__file__), '../docs/%s' % fname))
    text = open(doc_file, 'rb').read().decode('utf-8')
    doc_test = doctest.DocTestParser().get_doctest(text, {}, fname, fname, 0)
    return doctest.DocTestCase(doc_test, optionflags=doctest.ELLIPSIS)

suite = unittest.TestSuite()
for fname in ['note_format.txt', 'repository.txt', 'wsgi.txt']:
    suite.addTest(doctest_to_unittest(fname))

if __name__ == '__main__': unittest.TextTestRunner().run(suite)
