import logging
from zensols.nlp import FeatureDocument
from zensols.amr import AmrDocument, AmrFeatureDocument
from zensols.db.sqlite import SqliteConnectionManager
from util import TestBase

logger = logging.getLogger(__name__)


class TestParagraph(TestBase):
    def test_parse(self):
        self._config_logging()
        mng: SqliteConnectionManager = self.fac('mimic_sqlite_conn_manager')
        if not mng.db_file.exists():
            logger.warning('no MIMIC-III database to test with--skipping')
            return
        stash: Stash = self.fac('mimic_corpus').hospital_adm_stash
        return
        self.fac.config['mimic_corpus'].write()
        print()
        self.fac.config['mimic_note_event_persister'].write()
        print()
        self.fac.config['mimic_sqlite_conn_manager'].write()
        print(len(stash))
