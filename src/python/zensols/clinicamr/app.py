"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from typing import Tuple, Any
from dataclasses import dataclass, field
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.mimic import HospitalAdmission
from . import ClinicalAmrError, PlotMode, Plotter

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    plotter: Plotter = field()
    """Creates PDF plots of the AMR graphs."""

    def __post_init__(self):
        FeatureToken.WRITABLE_FEATURE_IDS = tuple('norm cui_'.split())

    def predict(self, text: str):
        """Predict clinical text.

        :param text: the text to parse

        """
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

    def _get_feasibility_report(self) -> pd.DataFrame:
        return self.plotter.get_feasibility_report(
            Path('feasibility/proofing.xlsx'), 'paul plots')

    def write_proof_report(self, output_path: Path = Path('proof-report.csv')):
        """Write the feasibility proof report, which writes only the analyzed
        AMR graphs.

        :param output_path: the path to write the report

        """
        df = self._get_feasibility_report()
        df.to_csv(output_path)
        logger.info(f'wrote: {output_path}')

    def report_stats(self):
        """Print feasibility report stats."""
        df = self._get_feasibility_report()
        dfg = df.groupby('model')['correctness']
        print('mean:')
        print(dfg.agg('mean'))
        print('\nstandard deviation:')
        print(dfg.agg(np.std))

    def _test_parse(self, clear_data: bool = False,
                    print_toks: bool = False,
                    dump: bool = True):
        from zensols.amr import AmrFeatureDocument
        if clear_data:
            p = Path('data')
            if p.is_dir():
                import shutil
                shutil.rmtree(p)

        sent = """58 y/o M with multiple myeloma s/p chemo and auto SCT [**4-27**]
presenting with acute onset of CP and liver failure"""
        doc: AmrFeatureDocument = self.doc_parser(sent)
        if print_toks:
            for i, t in enumerate(doc.tokens):
                print(f'<{i}/{t.i_sent}>: <{t.norm}/{t.text}>, <{t.ent_} ({t.cui_})>')
            print('_' * 40)
        doc.amr.write()
        if dump:
            dumper = self.config_factory('amr_dumper')
            dumper.render(doc.amr)

    def _test_paragraphs(self):
        from typing import Dict
        from zensols.mimic import Section, Note
        from zensols.mimic.regexnote import DischargeSummaryNote
        from zensols.amr import AmrFeatureDocument

        if 0:
            self.config_factory('clear_cli').clear()
        dumper = self.config_factory('amr_dumper')
        hadm_id: str = '134891'
        stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        if len(ds_notes) == 0:
            raise ClinicalAmrError(
                f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        sec: Section = ds_note.sections_by_name['history-of-present-illness'][0]
        if 0:
            print(sec.text)
            print('_' * 80)
        if 1:
            paras = tuple(sec.paragraphs)
            para: AmrFeatureDocument
            for para in paras:
                #para.write(sent_kwargs=dict(include_metadata=True))
                print(para.text)
                print()
            if 0:
                for t in paras[0][1]:
                    print(t, t.cui_, t.ent_, t.is_concept)
            if 0:
                for para in paras:
                    dumper.render(para.amr)

    def _tmp(self):
        pass

    def proto(self, run: int = 3):
        """Used for rapid prototyping."""
        {0: self._tmp,
         1: lambda: self.plot(limit=1, mode=PlotMode.by_paragraph),
         2: self.write_proof_report,
         3: self._test_parse,
         4: self._test_paragraphs,
         }[run]()
