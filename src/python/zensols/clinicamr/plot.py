"""Plot AMR graphs using various models.

"""
__author__ = 'Paul Landes'

from typing import Iterable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import sys
import logging
import re
from pathlib import Path
import itertools as it
import pandas as pd
from zensols.util import APIError
from zensols.config import Configurable
from zensols.persist import Stash
from zensols.nlp import FeatureSentence, FeatureDocument
from zensols.amr import AmrFeatureSentence, AmrFeatureDocument
from zensols.mimic import Corpus, Note, Section, HospitalAdmission
from zensols.mimicsid import AnnotationResource

logger = logging.getLogger(__name__)


class PlotMode(Enum):
    by_admission = auto()
    by_paragraph = auto()


@dataclass
class Plotter(object):
    config: Configurable = field()
    """The configurable used to create this instance."""

    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field()
    """Contains resources to access the MIMIC-III MedSecId annotations."""

    plot_path: Path = field()
    """Base path to add AMR graphs."""

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
                                             note.category, sec.id, sent.norm))
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
        parser_model: str = self.config.get_option(
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

    def get_sent(self, hadm_id: str, sent_id: str) -> FeatureSentence:
        """Return a the sentence that was used to create an entry in the plot
        feasibility proofing Excel file.

        :param hadm_id: the hospital admission ID

        :param sent_id:

             the sentence ID string, which has the form:
             ``<note row_id>-<section id>-<paragraph idx>-<sentence idx>``

        """
        m: re.Match = re.match(r'^(\d+)-(.+)-(\d+)-(\d+)$', sent_id)
        row_id, sec_id, par_id, sent_id = m.groups()
        row_id, par_id, sent_id = int(row_id), int(par_id), int(sent_id)
        adm: HospitalAdmission = self.corpus.hospital_adm_stash[hadm_id]
        note: Note = adm[row_id]
        sec: Section = note[sec_id]
        para: FeatureDocument = sec.paragraphs[par_id]
        sent: FeatureSentence = para[sent_id]
        return sent

    def get_feasibility_report(self, feas_excel_path: Path, sheet_name: str):
        assert_len = 20
        df = pd.read_excel(feas_excel_path, sheet_name=sheet_name)
        df = df.rename(columns={'how correct': 'correctness'})
        df = df[~df['correctness'].isnull()]
        rows: List[Tuple] = []
        for _, row in df.iterrows():
            sid = row['id']
            try:
                sent = self.get_sent(row['hadm_id'], sid)
            except Exception as e:
                logger.error(f'Could not get sentence: {sid}: {e}')
                continue
            org_sent = str(row['sent'])[:assert_len]
            match_sent = sent.text[:assert_len]
            if org_sent != match_sent:
                raise APIError(f'Sentences mismatch: {org_sent} != ' +
                               f'{match_sent} for {sid}')
            nrow = [row[k] for k in 'id correctness issues '.split()]
            nrow.append(re.match(r'^([^\/]+)', row['file']).group(1))
            nrow.append(sent.norm)
            rows.append(nrow)
        cols = 'id correctness issues model sent'.split()
        return pd.DataFrame(rows, columns=cols)
