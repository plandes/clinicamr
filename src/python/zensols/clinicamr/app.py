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
    CLI_META = {'option_includes': set('text hadm_id'.split())}

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
                        logger.warning(f'Error creating plot: {e}--skipping')

    def _tmp(self):
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash['119960']
        note = adm.notes_by_category['Physician'][0]
        #print(note.text)
        sec = note.sections['review-of-systems']
        print(f'header: <{sec.header}>')
        print(f'body: <{sec.body}>')
        print(f'norm: <{sec.body_doc.norm}>')
        sec.body_doc.write()
        for t in sec.body_doc.tokens:
            print('T', t)
        ann = self.config_factory('amr_annotator')
        from zensols.util import loglevel
        with loglevel('zensols.amr'):
            doc = ann(sec.body_doc)
        doc.write()
        return
        para = sec.paragraphs[0]
        para.write()
        #print(para.amr.graph_string)
        #para.amr.plot()

    def _tmp(self):
        #doc = self.doc_parser('he had no changes')
        text = """Mr. [**Known lastname **] is an 87 yo male with a
history of diastolic CHF (EF\n65% 1/10)."""
        doc = self.doc_parser(text)
        doc.write()
        ann = self.config_factory('amr_annotator')
        doc = ann(doc)
        #doc.write()
        print(doc.amr.graph_string)

    def proto(self):
        """Used for rapid prototyping."""
        if 0:
            self.clear()
        #self.plot(limit=1)
        self._tmp()
