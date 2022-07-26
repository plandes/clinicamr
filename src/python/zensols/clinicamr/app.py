"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
import re
from pathlib import Path
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.mimic import Note, Section, HospitalAdmission
from . import PlotMode, Plotter

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    CLI_META = {'option_includes':
                set('text hadm_ids annotators limit mode delete run'.split())}

    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    plotter: Plotter = field()
    """Creates PDF plots of the AMR graphs."""

    amr_paragraph_stash: Stash = field()
    """The stash that caches paragraph AMR graphs."""

    def __post_init__(self):
        FeatureToken.WRITABLE_FEATURE_IDS = tuple('norm cui_'.split())

    def parse(self, text: str = None):
        """Parse a MIMIC-III string.

        :param text: the text to parse

        """
        text = 'He died of liver failure.' if text is None else text
        doc = self.doc_parser(text)
        doc.sents[0].write()
        sent = doc.sents[0]
        if hasattr(sent, 'amr'):
            print(doc.amr)
            doc.amr.plot(Path('/d/amr'))

    def plot(self, hadm_ids: str = None, limit: int = None,
             mode: PlotMode = PlotMode.by_admission,
             annotators: str = 'kunal,adam,paul'):
        """Create plots for an admission.

        :param hadm_id: the admission ID

        :param limit: the max number of notes to plot

        :param mode: the plot file system and tracking strategy

        :param annotators: the human annotators used to divide the work in
                           sheets

        """
        self.plotter.plot(hadm_ids, limit, mode, annotators)

    def clear(self):
        """Clear the paragraph AMR cache."""
        logger.info(f'removing files in: {self.amr_paragraph_stash.path}')
        self.amr_paragraph_stash.clear()

    def _tmp1(self):
        """Used for rapid prototyping."""
        hadm_id = '119960'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note = adm.notes_by_category['Discharge summary'][0]
        sec = note.sections['history-of-present-illness']
        for para in sec.paragraphs:
            para.amr.plot(self.plot_path / f'{adm.hadm_id}-{note.row_id}')

    def _tmp(self):
        sec_name = 'history-of-present-illness'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash['119960']
        note = adm.notes_by_id[532411]
        sec = note.sections[sec_name]
        for p in sec.paragraphs[0:1]:
            p.amr.plot(top_to_bottom=False, front_text='Testing')

    def _tmp(self):
        stash = self.amr_paragraph_stash
        for doc in stash.values():
            for sent in doc.sents:
                print('-', sent.text)

    def _tmp(self):
        hadm_id = '120842'
        k = '523069-24-hour-events-0-0'
        #k = '522936-disposition-0-0'
        #k = '522936-communication-0-0'
        m = re.match(r'^(\d+)-(.+)-\d+-\d+$', k)
        row_id, sec_id = m.groups()
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note: Note = adm[int(row_id)]
        sec: Section = note.sections[sec_id]
        if 0:
            print(note.text)
            print('_' * 120)
        print(sec.header)
        print('-' * 80)
        print(sec.body)
        print('-' * 80)
        print(sec.body_doc.text)
        print('-' * 80)
        print(sec.body_doc.norm)
        print('-' * 80)
        for para in sec.paragraphs:
            print(para.norm)
            print('sents:')
            for sent in para.sents:
                print(sent.norm)
                print('-' * 20)
            print('-' * 30)

    def proto(self, run: int = 0):
        """Used for rapid prototyping."""
        {0: lambda: self.plot(limit=1, mode=PlotMode.by_paragraph),
         1: self._tmp,
         }[run]()
