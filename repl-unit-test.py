#!/usr/bin/env python

import logging
from pathlib import Path
from zensols.introspect.tester import UnitTester


def main():
    testrun = UnitTester('test_parser', Path('test/python'))
    testrun()


if (__name__ == '__main__'):
    logging.basicConfig()
    logging.getLogger('tester').setLevel(logging.INFO)
    main()
