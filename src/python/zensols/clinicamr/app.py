"""Clincial Domain Abstract Meaning Representation Graphs

"""
from __future__ import annotations
__author__ = 'Paul Landes'
from typing import List, Tuple
from dataclasses import dataclass, field
import logging
from pathlib import Path
import pandas as pd
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.cli import ApplicationError
from zensols.nlp import FeatureToken, FeatureDocumentParser

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    adm_amr_stash: Stash = field()
    """A stash that CRUDs instances of :obj:`.AdmissionAmrFeatureDocument`."""

    dumper: 'Dumper' = field()
    """Plots and writes AMR content in human readable formats."""

    def __post_init__(self):
        FeatureToken.WRITABLE_FEATURE_IDS = tuple('norm cui_'.split())

    def show_admission(self, hadm_id: str):
        """Print an admission by ID.

        :param hadm_id: the admission ID

        """
        from . import AdmissionAmrFeatureDocument
        from .adm import AdmissionAmrFactoryStash
        stash: AdmissionAmrFactoryStash = self.adm_amr_stash
        adm: AdmissionAmrFeatureDocument = stash.load(hadm_id)
        adm.write()

    def _generate_adm(self, hadm_id: str) -> pd.DataFrame:
        from typing import List, Dict, Any
        from zensols.mimic import Section, Note, HospitalAdmission
        from zensols.mimic.regexnote import DischargeSummaryNote
        from zensols.amr import (
            AmrFeatureSentence, AmrFeatureDocument,
            AmrGeneratedSentence, AmrGeneratedDocument,
        )
        from zensols.amr.model import AmrGenerator

        if logger.isEnabledFor(logging.INFO):
            logger.info(f'generating admission {hadm_id}')
        generator: AmrGenerator = self.config_factory('amr_generator_amrlib')
        stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        if len(ds_notes) == 0:
            raise ApplicationError(
                f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'generating from note {ds_note}')
        rows: List[Tuple[Any, ...]] = []
        cols: List[str] = 'hadm_id note_id sec_id sec_name org gen'.split()
        sec: Section
        for sec in ds_note.sections.values():
            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    f'generating sentences for section {sec.name} ({sec.id})')
            para: AmrFeatureDocument
            for para in sec.paragraphs:
                gen_para: AmrGeneratedDocument = generator(para.amr)
                assert len(gen_para) == len(para)
                sent: AmrFeatureSentence
                gen_sent: AmrGeneratedSentence
                for sent, gen_sent in zip(para, gen_para):
                    rows.append((hadm_id, ds_note.row_id, sec.id, sec.name,
                                 sent.norm, gen_sent.text))
        return pd.DataFrame(rows, columns=cols)

    def generate(self, ids: str, output_dir: Path = None):
        """Creates samples of generated AMR text by first parsing clinical
        sentences into graphs.

        :param ids: a comma separated list of admission IDs to generate

        :param output_dir: the output directory

        """
        if output_dir is None:
            output_dir = self.dumper.target_dir
        output_path = output_dir / 'generated-sents.csv'
        hadm_ids: List[str] = ids.split(',')
        dfs: Tuple[pd.DataFrame] = tuple(map(self._generate_adm, hadm_ids))
        df: pd.DataFrame = pd.concat(dfs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path)
        logger.info(f'wrote: {output_path}')


@dataclass
class PrototypeApplication(object):
    CLI_META = {'is_usage_visible': False}

    config_factory: ConfigFactory = field()
    app: Application = field()

    def _clear(self, only_para: bool = False):
        if only_para:
            self.config_factory('camr_paragraph_factory').clear()
            self.config_factory('camr_adm_amr_stash').clear()
        else:
            self.config_factory('clear_cli').clear()

    def _test_load(self):
        from zensols.util.time import time
        from zensols.clinicamr.adm import AdmissionAmrFactoryStash
        #self._clear(1)
        self._clear()
        stash: AdmissionAmrFactoryStash = self.config_factory('camr_adm_amr_stash')
        #hadm_id: str = '134891'  # human annotated
        hadm_id: str = '151608'  # model annotated
        with time('loaded'):
            adm = stash.load(hadm_id)
        #adm.write()
        for s in adm.sents:
            s.amr.write()

    def _tmp(self):
        pass

    def proto(self, run: int = 1):
        """Used for rapid prototyping."""
        {0: self._tmp,
         1: self._test_load,
         }[run]()
