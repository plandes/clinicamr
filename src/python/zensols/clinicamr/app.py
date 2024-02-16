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

    def _test_parse(self):
        if 0:
            self.config_factory.config['map_filter_token_normalizer'].write()
            return
        from zensols.amr import AmrFeatureDocument
        sent = 'Pt is a 73-year-old female in Dallas with COPD/RAD on home O2, diastolic CHF, recent TKR, presenting with respiratory distress and tachycardia, perscribe paxil 2/day.'
        #parser = self.doc_parser
        #parser = self.config_factory('doc_parser')
        parser = self.config_factory('mednlp_combine_biomed_doc_parser')
        #parser = self.config_factory('mednlp_biomed_parser')
        if 0:
            from scispacy.abbreviation import AbbreviationDetector
            parser.model.add_pipe("abbreviation_detector")
        if 0:
            print(parser.model.name)
        doc: AmrFeatureDocument = parser(sent)
        if 0:
            self.config_factory.config['mednlp_combine_biomed_doc_parser'].write()
        if 0:
            for t in doc.tokens:
                print(t, t.ent_, t.pos_, t.tag_)
            return
        if 1:
            for t in doc.tokens:
                print(t, t.is_concept, t.ent_, t.cui_, t.is_concept)
            return
        if 1:
            print(isinstance(doc, AmrFeatureDocument))
            doc.amr.write()
            dumper = self.config_factory('amr_dumper')
            dumper.render(doc.amr)

    def _test_paragraphs(self):
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

    def _tmp(self):
        #self.config_factory('clear_cli').clear()
        self.config_factory.config.write()

    def proto(self, run: int = 3):
        """Used for rapid prototyping."""
        {0: self._tmp,
         1: lambda: self.plot(limit=1, mode=PlotMode.by_paragraph),
         2: self.write_proof_report,
         3: self._test_parse,
         4: self._test_paragraphs,
         }[run]()
