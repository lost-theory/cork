import unittest
import doctest
from os.path import dirname, join
from os import listdir

doctest_dir = join(dirname(__file__), '../docs/')

def doctest_to_unittest(fname):
    doc_file = join(doctest_dir, fname)
    text = open(doc_file, 'rb').read().decode('utf-8')
    doc_test = doctest.DocTestParser().get_doctest(text, {}, fname, fname, 0)
    return doctest.DocTestCase(doc_test, optionflags=doctest.ELLIPSIS)

suite = unittest.TestSuite()

for fname in listdir(doctest_dir):
    if fname.endswith('.txt'):
        suite.addTest(doctest_to_unittest(fname))

if __name__ == '__main__': unittest.TextTestRunner().run(suite)
