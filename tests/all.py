""" Run all tests """

import os
import unittest

fnames = map(os.path.splitext, os.listdir(os.path.split(__file__)[0]))
modules = [base for base, ext in fnames if ext == '.py' and base.startswith('test_')]

suite = unittest.TestSuite()
suite.addTests(unittest.TestLoader().loadTestsFromNames(modules))

from doctests import suite as doctests_suite
suite.addTests(doctests_suite)

if __name__ == '__main__': unittest.TextTestRunner().run(suite)
