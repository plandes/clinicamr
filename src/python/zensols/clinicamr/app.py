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
from . import ClinicalAmrError, PlotMode, Plotter

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

    def _test_parse(self):
        from zensols.amr import AmrFeatureDocument
        #self._test_paragraphs()
        #self.report_stats()
        sent = '73-year-old female in Dallas with COPD/RAD on home O2, diastolic CHF, recent TKR, presenting with respiratory distress and tachycardia.'
        #print(id(self.config_factory('camr_doc_parser')) == id(self.doc_parser))
        #return
        doc: AmrFeatureDocument = self.doc_parser(sent)
        if 1:
            for t in doc.tokens:
                print(t, t.is_concept, t.ent_, t.cui_, t.is_concept)
        if 1:
            print(isinstance(doc, AmrFeatureDocument))
            doc.amr.write()
            dumper = self.config_factory('amr_dumper')
            dumper.render(doc.amr)

    def _tmp(self):
        from typing import Dict, Tuple
        from zensols.mimic import Section, Note
        from zensols.mimic.regexnote import DischargeSummaryNote
        from zensols.amr import AmrFeatureDocument

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
            for para in paras[0:1]:
                para.write(sent_kwargs=dict(include_metadata=True))
            if 1:
                for t in paras[0][1]:
                    print(t, t.cui_, t.ent_, t.is_concept)

    def proto(self, run: int = 0):
        """Used for rapid prototyping."""
        {0: self._tmp,
         1: lambda: self.plot(limit=1, mode=PlotMode.by_paragraph),
         2: self.write_proof_report,
         3: self._test_parse,
         }[run]()
