"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List
from dataclasses import dataclass, field
import sys
import logging
import itertools as it
from zensols.nlp import FeatureDocument
from zensols.amr import AmrFeatureDocument, AmrDocumentAnnotator
from zensols.mimic import ParagraphFactory, Section

logger = logging.getLogger(__name__)


@dataclass
class ClinicAmrParagraphFactory(ParagraphFactory):
    """Parse paragraph AMR graphs by using the super class paragraph factory.  Then
    each document is given an AMR graph using a
    :class:`~zensols.amr.AmrDocument` at the document level and a
    :class:`~zensols.amr.AmrSentence` at the sentence level, which are are
    cached using a :class:`~zensols.persist.Stash`.

    A list of :class:`~zensols.amr.AmrFeatureDocument` are returned.

    """
    amr_annotator: AmrDocumentAnnotator = field()
    """Parses, populates and caches AMR graphs in feature documents."""

    limit: int = field(default=sys.maxsize)

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        paras: List[FeatureDocument] = super().__call__(sec)
        amr_paras: List[AmrFeatureDocument] = []
        para: FeatureDocument
        for pix, para in enumerate(it.islice(paras, self.limit)):
            key = f'{sec._row_id}-{sec.id}-{pix}'
            amr_doc: AmrFeatureDocument = self.amr_annotator(para, key)
            amr_doc.key = key
            amr_paras.append(amr_doc)
        return amr_paras
