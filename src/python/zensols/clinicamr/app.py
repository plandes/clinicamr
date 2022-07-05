"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from typing import Iterable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
import logging
import re
import shutil
from pathlib import Path
import itertools as it
import pandas as pd
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.amr import AmrFeatureSentence, AmrFeatureDocument
from zensols.mimic import Corpus, Note, Section, HospitalAdmission
from zensols.mimicsid import AnnotationResource

logger = logging.getLogger(__name__)


class PlotMode(Enum):
    by_admission = auto()
    by_paragraph = auto()


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    CLI_META = {'option_includes': set('text hadm_id limit run'.split())}

    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field()
    """Contains resources to access the MIMIC-III MedSecId annotations."""

    plot_path: Path = field()
    """Base path to add AMR graphs."""

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

    def _plot_section(self, sec: Section, note: Note, mode: PlotMode,
                      note_path: Path, rows: List):
        if len(sec.body_doc.norm) > 0:
            if logger.isEnabledFor(logging.INFO):
                logger.info(f'creating plots for section: {sec}')
            try:
                para: AmrFeatureDocument
                for para in sec.paragraphs:
                    if mode == PlotMode.by_admission:
                        front_text = f'Note IDX: {note.row_id}, sec: {sec.id};'
                        para.amr.plot(note_path, front_text=front_text)
                    else:
                        sent: AmrFeatureSentence
                        for sent in para.sents:
                            pix = len(rows)
                            target_file_name = f'{pix}.pdf'
                            pdf_file = note_path / target_file_name
                            rows.append((pix, str(pdf_file), sent.text))
                            sent.amr.plot(
                                note_path,
                                target_file_name=target_file_name,
                                front_text=f'[{pix}]',
                                write_text=False)
            except Exception as e:
                logger.warning('Error creating plot for note ' +
                               f'{note.row_id}: {e}--skipping')

    def plot(self, hadm_ids: str = '119960', limit: int = None,
             mode: PlotMode = PlotMode.by_admission, delete: bool = True):
        """Create plots for an admission.

        :param hadm_id: the admission ID

        :param limit: the max number of plots to create

        :param mode: the plot file system and tracking strategy

        :param delete: delete any previous plots if they exist

        """
        limit = sys.maxsize if limit is None else limit
        parser_model: str = self.config_factory.config.get_option(
            'parse_model', section='amr_default')
        df: pd.DataFrame = self.anon_resource.note_ids
        stash: Stash = self.corpus.hospital_adm_stash
        rows: List = []
        if self.plot_path.is_dir():
            logger.info(f'removing previous plots: {self.plot_path}')
            shutil.rmtree(self.plot_path)
        for hadm_id in re.split(r'\s*,\s*', hadm_ids):
            adm: HospitalAdmission = stash[hadm_id]
            anon_row_ids = df[df['hadm_id'] == hadm_id]['row_id'].\
                astype(int).tolist()
            notes: Iterable[Note] = it.islice(
                map(lambda i: adm.notes_by_id[i], anon_row_ids), limit)
            for note in notes:
                id_dir: str = f'{adm.hadm_id}-{note.row_id}'
                note_path: Path = self.plot_path / parser_model
                if mode == PlotMode.by_admission:
                    note_path = note_path / id_dir
                note_path.mkdir(parents=True, exist_ok=True)
                logger.info(f'creating plots for note: {note}')
                sec: Section
                for sec in note.sections.values():
                    self._plot_section(sec, note, mode, note_path, rows)
        if mode == PlotMode.by_paragraph:
            df = pd.DataFrame(rows, columns='id file sent'.split())
            df.to_csv(self.plot_path / f'{parser_model}.csv')

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

    def proto(self, run: int = 0):
        """Used for rapid prototyping."""
        {0: lambda: self.plot(limit=2, mode=PlotMode.by_paragraph),
         1: self._tmp,
         }[run]()
