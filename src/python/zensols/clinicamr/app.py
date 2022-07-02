"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from typing import Iterable
from dataclasses import dataclass, field
import sys
import logging
from pathlib import Path
import itertools as it
import pandas as pd
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.mimic import Corpus, Note, HospitalAdmission
from zensols.mimicsid import AnnotationResource

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    CLI_META = {'option_includes': set('text hadm_id limit'.split())}

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

    def plot(self, hadm_id: str = '119960', limit: int = None):
        """Create plots for an admission.

        :param hadm_id: the admission ID

        :param limit: the max number of plots to create

        """
        limit = sys.maxsize if limit is None else limit
        parser_model: str = self.config_factory.config.get_option(
            'parse_model', section='amr_default')
        df: pd.DataFrame = self.anon_resource.note_ids
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        anon_row_ids = df[df['hadm_id'] == hadm_id]['row_id'].\
            astype(int).tolist()
        notes: Iterable[Note] = it.islice(
            map(lambda i: adm.notes_by_id[i], anon_row_ids), limit)
        for note in notes:
            id_dir: str = f'{adm.hadm_id}-{note.row_id}'
            note_path: Path = self.plot_path / parser_model / id_dir
            logger.info(f'creating plots for note: {note}')
            for sec in note.sections.values():
                if len(sec.body_doc.norm) > 0:
                    logger.info(f'creating plots for section: {sec}')
                    try:
                        for para in sec.paragraphs:
                            para.amr.plot(note_path)
                    except Exception as e:
                        logger.warning('Error creating plot for note ' +
                                       f'{note.row_id}: {e}--skipping')

    def _tmp(self):
        sec_name = 'history-of-present-illness'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash['119960']
        note = adm.notes_by_id[532411]
        sec = note.sections[sec_name]
        for p in sec.paragraphs:
            print(type(p))
            print(p)
        return
        for note in adm.notes_by_category['Physician']:
            if sec_name in note.sections:
                print(note)
                norm = note.doc.norm
                found_unmatch_tok = norm.find('**') > -1
                found_unmatch_ent = norm.find('<UNKNOWN>') > -1
                if found_unmatch_tok or found_unmatch_ent:
                    print('original:')
                    print(note.doc.text)
                    print('norm:')
                    print(norm)
                print('_' * 120)
        return

    def proto(self):
        """Used for rapid prototyping."""
        #self.plot(limit=1)
        self._tmp()
