import unittest
import sys
from pathlib import Path
import shutil
from zensols.config import ImportIniConfig, ImportConfigFactory


class TestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = sys.maxsize
        super().__init__(*args, **kwargs)
        conf = ImportIniConfig('test-resources/test.conf')
        self.fac = ImportConfigFactory(conf)
        targ_dir = Path('target')
        if targ_dir.is_dir():
            shutil.rmtree(targ_dir)

    def _config_logging(self):
        import logging
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger('zensols.amr').setLevel(logging.DEBUG)
