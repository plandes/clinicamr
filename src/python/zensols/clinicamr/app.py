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

    def _create_paragraphs(self, sec):# -> List[FeatureDocument]:
        import itertools as it
        from spacy.tokens import Doc
        from zensols.nlp import FeatureDocument, FeatureSentence

        self = sec
        paras = self._create_paragraphs()

        para: FeatureDocument
        for para in it.islice(paras, 1):
            doc: Doc = self._doc_parser.to_spacy_doc(
                para, add_features=set('pos tag lemma'.split()))

            for t in doc:
                if t.lemma_.find('\n') > -1:
                    t.lemma_ = t.orth_
                else:
                    pos = t.lemma_.find(' ')
                    if pos > -1:
                        t.lemma_ = t.lemma_[:pos]

            print(doc.text)
            self._amr_parser(doc)
            sent: FeatureSentence
            for sent, span in zip(para, doc.sents):
                print('S', sent)
                print(span._.amr.graph_string)
                print('-' * 80)
            
    def proto(self):
        import amrlib
        hadm_id = '119960'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note = adm.notes_by_category['Discharge summary'][0]
        sec = note.sections['history-of-present-illness']
        sec._doc_parser = self.doc_parser
        sec._amr_parser = self.config_factory('amr_parser')
        self._create_paragraphs(sec)
        return
        doc = self.doc_parser.parse_spacy_doc("""AFib not on coumadin , mild AS , stage IV CKD , and HTN , who presented from acute rehab after falling at his nursing home .""")
        gr = amrlib.spacy_stog_span(doc)
        print(len(gr))
        print(gr[0])
