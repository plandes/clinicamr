from __future__ import annotations
"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List, Tuple, Type
from dataclasses import dataclass, field
import logging
from zensols.persist import Stash
from zensols.nlp import FeatureDocument
from zensols.amr import (
    AmrParser, AmrDocument, AmrFeatureSentence, AmrFeatureDocument,
    TokenIndexMapper, TokenFeaturePopulator,
)
from zensols.mimic import ParagraphFactory, Section
from . import SpacyDocAdapter

logger = logging.getLogger(__name__)


@dataclass
class AmrDocumentAnnotator(object):
    amr_parser: AmrParser = field()
    """The AMR parser used to induce the graphs."""

    token_index_mapper: Tuple[TokenIndexMapper] = field(default=None)
    """Adds token indicies to the AMR."""

    token_feature_populators: Tuple[TokenFeaturePopulator] = field(default=())
    """Populates the AMR graph with a feature."""

    stash: Stash = field(default=None)
    """Used to store the :class:`~zensols.amr.AmrDocument` instances."""

    doc_class: Type[AmrFeatureDocument] = field(default=AmrFeatureDocument)
    """The :class:`~zensols.nlp.FeatureDocument` class created to store
    :class:`zensols.amr.AmrDocument` instances.

    """
    sent_class: Type[AmrFeatureSentence] = field(default=AmrFeatureSentence)
    """The :class:`~zensols.nlp.FeatureSentence` class created to store
    :class:`zensols.amr.AmrSentence` instances.

    """
    def _create_amr_doc(self, para: FeatureDocument) -> AmrDocument:
        doc = SpacyDocAdapter(para)
        self.amr_parser(doc)
        for sa, sd in zip(doc.sents, doc.sents):
            sa._.amr = sd._.amr
        if self.token_index_mapper is not None:
            self.token_index_mapper(doc)
        return doc._.amr

    def __call__(self, doc: FeatureDocument, key: str = None) -> AmrFeatureDocument:
        amr_doc: AmrDocument = None
        if self.stash is not None and key is not None:
            self.stash.load(key)
        stash_miss = amr_doc is None
        if amr_doc is None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'parsing: {key} -> {doc}')
            amr_doc = self._create_amr_doc(doc)
        amr_doc: AmrDocument
        fsents: List[AmrFeatureSentence] = []
        for amr_sent, psent in zip(amr_doc.sents, doc.sents):
            amr_fsent = psent.clone(self.sent_class, amr=amr_sent)
            fsents.append(amr_fsent)
        amr_fdoc: AmrFeatureDocument = doc.clone(
            self.doc_class, sents=fsents, amr=amr_doc)
        if stash_miss:
            for populator in self.token_feature_populators:
                populator(amr_fdoc)
            if self.stash is not None and key is not None:
                self.stash.dump(key, amr_doc)
        return amr_fdoc


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

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        import itertools as it
        amr_paras: List[AmrFeatureDocument] = []
        para: FeatureDocument
        for pix, para in enumerate(it.islice(super().__call__(sec), 2)):
            key = f'{sec._row_id}-{sec.id}-{pix}'
            amr_paras.append(self.amr_annotator(para, key))
        return amr_paras
