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

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs

    """
    CLI_META = {
        'option_excludes':
        set('config_factory doc_parser corpus anon_resource'.split())}

    config_factory: ConfigFactory = field()
    """
    """
    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field()
    """Contains resources to acces the MIMIC-III MedSecId annotations."""

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

    def proto(self):
        """Used for rapid prototyping."""
        hadm_id = '119960'
        base_path = Path('amr-doc')
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note = adm.notes_by_category['Discharge summary'][0]
        sec = note.sections['history-of-present-illness']
        #print(sec.body)
        if 1:
            for para in sec.paragraphs:
                print(para.amr)
                para.amr.plot(base_path / para.key)
        else:
            print(note.doc.norm)
            return
            for para in sec.paragraphs:
                print(para.norm)
                print('--')

    def protoX(self):
        s = """Mr. [**Known lastname **] is an 87 yo male with a history of diastolic CHF (EF\n65% 1/10)."""
        ann = self.config_factory('amr_annotator')
        doc = self.doc_parser(s)
        print(ann(doc).amr.graph_string)
