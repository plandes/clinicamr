import unittest
import os
import sys
from pathlib import Path
from io import BytesIO
import pickle
import shutil
import logging
from zensols.db.sqlite import SqliteConnectionManager
from zensols.persist import persisted
from zensols.clinicamr import ApplicationFactory
from zensols.mednlp import surpress_warnings

logger = logging.getLogger(__name__)


class TestBase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = sys.maxsize
        surpress_warnings()
        os.environ.pop('CLINICAMRRC', None)
        self._clear_cache()

    @property
    @persisted('_config_factory')
    def config_factory(self):
        from zensols.cli import CliHarness
        harness: CliHarness = ApplicationFactory.create_harness()
        return harness.get_config_factory(
            '-c test-resources/test.conf --level err')

    @property
    def doc_parser(self) -> 'FeatureDocumentParser':
        config_factory = self.config_factory
        sec: str = config_factory.config.get_option(
            'doc_parser', 'clinicamr_default')
        return config_factory(sec)

    def _validate_db_exists(self) -> bool:
        self._config_logging()
        mng: SqliteConnectionManager = \
            self.config_factory('mimic_sqlite_conn_manager')
        if not mng.db_file.exists():
            logger.error('no MIMIC-III database to test with--skipping')
            return False
        return True

    def _clear_cache(self):
        targ_dir = Path('target')
        if targ_dir.is_dir():
            shutil.rmtree(targ_dir)

    def _config_logging(self):
        logging.basicConfig(level=logging.ERROR)

    def _pickle(self, obj):
        bio = BytesIO()
        pickle.dump(obj, bio)
        bio.seek(0)
        return pickle.load(bio)
