from typing import Tuple, Dict
import sys
import logging
from io import TextIOBase, StringIO
from zensols.persist import Stash
from zensols.mimic import Section, Note, HospitalAdmission
from zensols.mimic.regexnote import DischargeSummaryNote
from zensols.amr import AmrFeatureDocument
from zensols.db.sqlite import SqliteConnectionManager
from util import TestBase

logger = logging.getLogger(__name__)

if 1:
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('zensols.nlp').setLevel(logging.INFO)


class TestParagraph(TestBase):
    """The medical parsers normalize out the MIMIC-III tokens, but that happens
    at the FeatureDocument level.  We cannot use that normalized text when
    parsing the AMR because amrlib expects spaCy spans (i.e. GSII expects it
    already tokenized).  The only way to do it is to create a spacy adapted
    (from feature document) span, then parse.

    The ``amrspring`` parser uses the MIMIC mapped singleton tokens from the
    MIMIC-III masked tokens in :mod:`zensols.clinicamr.spring`.

    """
    def _validate_db_exists(self) -> bool:
        self._config_logging()
        mng: SqliteConnectionManager = self.config_factory('mimic_sqlite_conn_manager')
        if not mng.db_file.exists():
            logger.warning('no MIMIC-III database to test with--skipping')
            return False
        return True

    def _test_parse(self):
        if self._validate_db_exists():
            self._test_parse()

    def _write_paras(self, paras: Tuple[AmrFeatureDocument],
                     writer: TextIOBase = sys.stdout):
        for para in paras:
            for i, sent in enumerate(para):
                if i > 0:
                    print('_' * 40, file=writer)
                print(sent.amr.metadata['id'], file=writer)
                print(sent.amr.metadata['snt'], file=writer)
                print(sent.amr.graph_only, file=writer)
            print('_' * 79, file=writer)

    def test_parse(self):
        from zensols.nlp import FeatureDocumentParser
        FeatureDocumentParser._LOG_FORMAT = 'parse[{name}/{cls.__name__}]: {text}'

        if 0:
            stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
            parser = stash.doc_stash.factory.doc_parser
            print(type(parser))
            doc = parser('He died of liver failure.')
            doc.write()
            for t in doc.token_iter():
                print(t, t.cui_, t.is_concept)
            return
        if 0:
            #parser = self.doc_parser
            parser = self.config_factory('mimic_note_event_persister_parser_stash').doc_parser
            print(parser, type(parser))
            doc = parser('He died of liver failure.')
            doc.write()
            for t in doc.token_iter():
                print(t, t.cui_, t.is_concept)
            return
        if 0:
            parser = self.config_factory('mimic_note_event_persister_parser_stash')
            print(parser.doc_parser)
            return

        DEBUG: bool = 0
        WRITE: bool = 0
        hadm_id: str = '134891'
        stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        self.assertNotEqual(len(ds_notes), 0,
                            f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        self.assertEqual(16, len(ds_note.sections))
        secs: Tuple[Section] = ds_note.sections_by_name['history-of-present-illness']
        self.assertEqual(1, len(secs))
        sec: Section = secs[0]
        paras: Tuple[AmrFeatureDocument] = tuple(sec.paragraphs)
        self.assertEqual(2, len(paras))
        if DEBUG:
            self._write_paras(paras)
            return
        should_file = 'test-resources/amr-paras.txt'
        if WRITE:
            with open(should_file, 'w') as f:
                self._write_paras(paras, f)
        with open(should_file) as f:
            should = f.read()
        sio = StringIO()
        self._write_paras(paras, sio)
        self.assertEqual(should, sio.getvalue())
