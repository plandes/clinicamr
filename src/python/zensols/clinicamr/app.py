"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
from pathlib import Path
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.mimic import Corpus, HospitalAdmission
from zensols.mimicsid import AnnotationResource
from zensols.amr import AmrError

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs

    """
    config_factory: ConfigFactory
    doc_parser: FeatureDocumentParser

    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field()
    """Contains resources to acces the MIMIC-III MedSecId annotations."""

    def __post_init__(self):
        FeatureToken.WRITABLE_FEATURE_IDS = tuple('norm cui_'.split())

    def proto(self):
        """Prototype test."""
        if logger.isEnabledFor(logging.INFO):
            logger.info('do something more')
        print(type(self.doc_parser.target_parser))
        doc = self.doc_parser('He died of liver failure.')
        sent = doc.sents[0]
        sent.write(n_tokens=1000)
        print(doc.amr)
        doc.amr.plot(Path('/d/amr'))

    def protoX(self):
        hadm_id = '119960'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note = adm.notes_by_category['Discharge summary'][0]
        hpi = note.sections['history-of-present-illness']
        for sent in hpi.body_doc:
            print(f'<{sent.text}>')
            print(sent.amr)
            print('-' * 100)
           
    def proto(self):
        hadm_id = '119960'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note = adm.notes_by_category['Discharge summary'][0]
        sec = note.sections['history-of-present-illness']
        for para in sec.paragraphs:
            print(type(para), type(para.amr))
            print(para.amr)
            if 0:
                for s in para.amr.sents:
                    print(type(s), s)
                    print(s.graph_string)
                print('-' * 80)
            para.amr.plot()
