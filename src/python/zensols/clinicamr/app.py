"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from typing import Iterable, List, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
import logging
import re
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
    CLI_META = {'option_includes':
                set('text hadm_ids annotators limit mode delete run'.split())}

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
                for pix, para in enumerate(sec.paragraphs):
                    if mode == PlotMode.by_admission:
                        front_text = f'Note: {note.row_id}, sec: {sec.id};'
                        para.amr.plot(note_path, front_text=front_text)
                    else:
                        sent: AmrFeatureSentence
                        for six, sent in enumerate(para.sents):
                            gix = f'{note.row_id}-{sec.id}-{pix}-{six}'
                            target_file_name = f'{gix}.pdf'
                            t_file = f't5/{target_file_name}'
                            g_file = f'gsii/{target_file_name}'
                            for fpath in (t_file, g_file):
                                rows.append((gix, None, None, fpath,
                                             note.hadm_id, note.row_id,
                                             note.category, sec.id, sent.text))
                            logger.info(f'plotting {target_file_name}')
                            sent.amr.plot(
                                note_path,
                                target_file_name=target_file_name,
                                front_text=f'[{gix}]',
                                write_text=False)
            except Exception as e:
                logger.warning('Error creating plot for note ' +
                               f'{note.row_id}: {e}--skipping')

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
        if hadm_ids is None:
            hadm_ids = '119960,118659,118760,120842,108346,109181,110002,146230'
        annotators: List[str] = re.split(r'\s*,\s*', annotators)
        limit = sys.maxsize if limit is None else limit
        parser_model: str = self.config_factory.config.get_option(
            'parse_model', section='amr_default')
        df: pd.DataFrame = self.anon_resource.note_ids
        stash: Stash = self.corpus.hospital_adm_stash
        rows: List = []
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
            csv_file = self.plot_path / 'proofing.csv'
            excel_file = self.plot_path / 'proofing.xlsx'
            df = pd.DataFrame(
                rows, columns=('id how_correct issues file hadm_id ' +
                               'note_id category section sent').split())
            df["file"] = '=HYPERLINK("http://nlpdeep.cs.uic.edu:8080/proofing/'+df["file"]+'","'+df["file"]+'")'
            df.to_csv(csv_file)
            logger.info(f'wrote: {csv_file}')
            dfs: List[pd.DataFrame]
            if annotators is None:
                dfs = [df]
                annotators = ['None']
            else:
                dfs = []
                alen = len(annotators)
                chunk_size = int(len(df) / alen)
                start = 0
                for sl in range(alen):
                    end = start + chunk_size
                    dfs.append(df[start:end])
                    start = end
            with pd.ExcelWriter(excel_file) as writer:
                for ann, df in zip(annotators, dfs):
                    df.to_excel(writer, index=False, sheet_name=f'{ann} plots')
            logger.info(f'wrote: {excel_file}')

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
        {0: lambda: self.plot(limit=1, mode=PlotMode.by_paragraph),
         1: self._tmp,
         }[run]()
