import unittest
import os
import sys
from pathlib import Path
import shutil
from zensols.persist import persisted
#from zensols.config import ImportIniConfig, ImportConfigFactory
from zensols.clinicamr import ApplicationFactory


class TestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = sys.maxsize
        super().__init__(*args, **kwargs)
        os.environ.pop('CLINICAMRRC', None)
        #conf = ImportIniConfig('test-resources/test.conf')
        #self.fac = ImportConfigFactory(conf)
        self._clear_cache()

    @property
    @persisted('_config_factory')
    def config_factory(self):
        from zensols.cli import CliHarness
        harness: CliHarness = ApplicationFactory.create_harness()
        return harness.get_config_factory('-c test-resources/tmp.conf')

    @property
    def doc_parser(self) -> 'FeatureDocumentParser':
        config_factory = self.config_factory
        sec: str = config_factory.config.get_option('doc_parser', 'clinicamr_default')
        return config_factory(sec)

    def _clear_cache(self):
        targ_dir = Path('target')
        if targ_dir.is_dir():
            shutil.rmtree(targ_dir)

    def _config_logging(self):
        import logging
        logging.basicConfig(level=logging.WARNING)
        #logging.getLogger('zensols.amr').setLevel(logging.DEBUG)
