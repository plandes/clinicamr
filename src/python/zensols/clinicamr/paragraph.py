"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List, Set, Tuple
from dataclasses import dataclass, field
import sys
import logging
import itertools as it
from zensols.nlp import FeatureDocument, FeatureToken
from zensols.amr import (
    AmrFeatureDocument, AmrDocumentAnnotator, TokenFeatureAnnotator
)
from zensols.mimic import ParagraphFactory, Section

logger = logging.getLogger(__name__)


@dataclass
class ClinicTokenFeatureAnnotator(TokenFeatureAnnotator):
    """Override token feature annotation by adding CUI data.

    """
    def _format_feature_value(self, tok: FeatureToken) -> str:
        return f'{tok.pref_name_} ({tok.cui_})'
        return getattr(tok, self.feature_id)

    def _annotate_token(self, tok: FeatureToken, source: str,
                        feature_triples: Set[Tuple[str, str, str]]):
        # when we find a concept, add in the CUI if the token is a
        # concept
        if tok.is_concept:
            super()._annotate_token(tok, source, feature_triples)


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
    """Limit on number of paragraphs to process and useful for prototyping."""

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
