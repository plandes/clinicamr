from typing import Tuple, Dict
import sys
import logging
from io import TextIOBase
from zensols.persist import Stash
from zensols.mimic import Section, Note, HospitalAdmission
from zensols.mimic.regexnote import DischargeSummaryNote
from zensols.amr import AmrFeatureDocument
from zensols.db.sqlite import SqliteConnectionManager
from util import TestBase

logger = logging.getLogger(__name__)


class TestParagraph(TestBase):
    def _validate_db_exists(self) -> bool:
        self._config_logging()
        mng: SqliteConnectionManager = self.fac('mimic_sqlite_conn_manager')
        if not mng.db_file.exists():
            logger.warning('no MIMIC-III database to test with--skipping')
            return False
        return True

    def test_parse(self):
        if self._validate_db_exists():
            self._test_parse()

    def _clear_cache(self):
        pass

    def _write_paras(self, paras: Tuple[AmrFeatureDocument],
                     writer: TextIOBase):
        for para in paras:
            for sent in para:
                print(sent.amr.metadata['id'], file=writer)
                print(sent.amr.graph_only, file=writer)
            print('_' * 80, file=writer)

    def _test_parse(self):
        """The medical parsers normalize out the MIMIC-III tokens, but that
        happens at the FeatureDocument level.  We cannot use that normalized
        text when parsing the AMR because amrlib expects spaCy spans (i.e. GSII
        expects it already tokenized).  The only way to do it is to create a
        spacy adapted (from feature document) span, then parse.

        The ``amrspring`` parser uses the MIMIC mapped singleton tokens from the
        MIMIC-III masked tokens in :mod:`zensols.clinicamr.spring`.

        """
        DEBUG = 0
        WRITE = 1
        hadm_id: str = '134891'
        stash: Stash = self.fac('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        self.assertNotEqual(len(ds_notes), 0,
                            f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        if 0:
            ds_note.write()
            sec = ds_note.sections_by_name['physical-examination'][0]
            paras: Tuple[AmrFeatureDocument] = tuple(sec.paragraphs)
            print(paras[0].norm)
            print(paras[0].amr.graph_string)
            return
        self.assertEqual(16, len(ds_note.sections))
        secs: Tuple[Section] = ds_note.sections_by_name['history-of-present-illness']
        #secs: Tuple[Section] = ds_note.sections_by_name['allergies']
        self.assertEqual(1, len(secs))
        sec: Section = secs[0]
        paras: Tuple[AmrFeatureDocument] = tuple(sec.paragraphs)
        self.assertEqual(2, len(paras))
        if DEBUG:
            para: AmrFeatureDocument
            for para in paras:
                self.assertEqual(AmrFeatureDocument, type(para))
                print(para.text)
                print()
                print(para.amr.graph_string)
                print('_' * 80)
        should_file = 'test-resources/amr-paras.txt'
        if WRITE:
            self._write_paras(paras, sys.stdout)
            #with open(should_file, 'w') as f:
