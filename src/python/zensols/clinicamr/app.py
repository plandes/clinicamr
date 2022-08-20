"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.mimic import HospitalAdmission
from . import PlotMode, Plotter

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    CLI_META = {'option_excludes':
                set('config_factory doc_parser plotter'.split()),
                'option_overrides': {'output_path': {'long_name': 'output'}},
                'mnemonic_overrides': {'write_proof_report': 'proofrep'}}

    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    plotter: Plotter = field()
    """Creates PDF plots of the AMR graphs."""

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

    def _get_feasibility_report(self) -> pd.DataFrame:
        return self.plotter.get_feasibility_report(
            Path('feasibility/proofing.xlsx'), 'paul plots')

    def write_proof_report(self, output_path: Path = Path('proof-report.csv')):
        """Write the feasibility proof report, which writes only the analyzed AMR
        graphs.

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

    def clear(self):
        """Clear the paragraph AMR cache."""
        amr_paragraph_stash: Stash = self.config_factory('amr_paragraph_stash')
        logger.info(f'removing files in: {amr_paragraph_stash.path}')
        amr_paragraph_stash.clear()

    def _test_paragraphs(self):
        sec_name = 'history-of-present-illness'
        stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash['119960']
        note = adm.notes_by_id[532411]
        sec = note.sections[sec_name]
        for p in sec.paragraphs[0:1]:
            p.amr.plot(top_to_bottom=False, front_text='Testing')

    def _tmp(self):
        #self._test_paragraphs()
        #self.report_stats()
        sent = '73-year-old female with COPD/RAD on home O2, diastolic CHF, recent TKR, presenting with respiratory distress and tachycardia.'
        doc_parser = self.doc_parser
        #doc_parser.write()
        doc = doc_parser(sent)
        #doc.write()

    def proto(self, run: int = 0):
        """Used for rapid prototyping."""
        {0: self._tmp,
         1: lambda: self.plot(limit=1, mode=PlotMode.by_paragraph),
         2: self.write_proof_report,
         }[run]()
