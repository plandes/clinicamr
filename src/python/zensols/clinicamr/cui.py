"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List
from dataclasses import dataclass, field
import logging
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

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        nasc_paras: List[FeatureDocument] = super().__call__(sec)
        amr_paras: List[AmrFeatureDocument] = []
        para: FeatureDocument
        for pix, para in enumerate(nasc_paras):
            key = f'{sec._row_id}-{sec.id}-{pix}'
            amr_paras.append(self.amr_annotator(para, key))
        return amr_paras
