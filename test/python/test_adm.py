import logging
from io import StringIO
from pathlib import Path
from zensols.clinicamr.corpus import CorpusFactoryStash
from zensols.clinicamr import AdmissionAmrFeatureDocument
from util import TestBase

logger = logging.getLogger(__name__)


class TestAdmissionGraph(TestBase):
    """This test takes a long time and easily fails given the large comparison
    it makes.

    """
    def test_adm_graph(self):
        if self._validate_db_exists():
            self._test_adm_graph()

    def _test_adm_graph(self):
        WRITE: bool = 0
        should_file = Path('test-resources/should-graph.txt')
        stash: CorpusFactoryStash = self.config_factory(
            'camr_corpus_factory_stash')
        self.assertTrue(isinstance(stash, CorpusFactoryStash))
        #hadm_id: str = '134891'  # human annotated
        hadm_id: str = '151608'  # model annotated
        adm: AdmissionAmrFeatureDocument = stash.load(hadm_id)
        if WRITE:
            with open(should_file, 'w') as f:
                adm.write(writer=f)
        with open(should_file) as f:
            should: str = f.read()
        sio = StringIO()
        adm.write(writer=sio)
        actual: str = sio.getvalue()
        self.assertEqual(should, actual)
