import logging
from io import StringIO
from pathlib import Path
from zensols.clinicamr.adm import AdmissionAmrFactoryStash
from zensols.clinicamr import AdmissionAmrFeatureDocument
from util import TestBase

logger = logging.getLogger(__name__)


class TestAdmissionGraph(TestBase):
    """This test takes a long time and easily fails given the large comparison
    it makes.

    """
    def setUp(self):
        super().setUp()
        self.should_file = Path('test-resources/should-graph.txt')

    def test_adm_graph_create(self):
        if self._validate_db_exists():
            self._test_adm_graph_create()

    def test_pickle(self):
        if self._validate_db_exists():
            self._test_pickle()

    def _get_adm(self) -> AdmissionAmrFeatureDocument:
        stash: AdmissionAmrFactoryStash = self.config_factory(
            'camr_adm_amr_factory_stash')
        self.assertTrue(isinstance(stash, AdmissionAmrFactoryStash))
        #hadm_id: str = '134891'  # human annotated
        hadm_id: str = '151608'  # model annotated
        return stash.load(hadm_id)

    def _get_should(self) -> str:
        with open(self.should_file) as f:
            return f.read()

    def _test_adm_graph_create(self):
        adm: AdmissionAmrFeatureDocument = self._get_adm()
        if self.WRITE:
            with open(self.should_file, 'w') as f:
                adm.write(writer=f)
        should: str = self._get_should()
        sio = StringIO()
        adm.write(writer=sio)
        actual: str = sio.getvalue()
        self.assertEqual(should, actual)

    def _test_pickle(self):
        adm: AdmissionAmrFeatureDocument = self._get_adm()
        sio = StringIO()
        adm.write(writer=sio)
        should: str = sio.getvalue()

        adm2 = self._pickle(adm)
        self.assertNotEqual(id(adm), id(adm2))
        self.assertEqual(adm, adm2)

        sio = StringIO()
        adm2.write(writer=sio)
        actual: str = sio.getvalue()
        self.assertEqual(should, actual)
