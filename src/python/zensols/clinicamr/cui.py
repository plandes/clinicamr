from __future__ import annotations
"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List, Tuple, Type
from dataclasses import dataclass, field
import logging
from zensols.persist import Stash
from zensols.nlp import FeatureDocument, SpacyFeatureDocumentParser
from zensols.amr import (
    AmrParser, AmrDocument, AmrFeatureSentence, AmrFeatureDocument,
    TokenIndexMapper, TokenFeaturePopulator,
)
from zensols.mimic import ParagraphFactory, Section
from . import SpacyDocAdapter

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
    amr_parser: AmrParser = field()
    """The AMR parser used to induce the graphs."""

    doc_parser: SpacyFeatureDocumentParser = field()
    """The parser used to convert super class (see class docs) documents back in
    spaCy :class:`~spacy.tokens.Doc` instances.

    """
    sec_para_stash: Stash = field()
    """Used to store the :class:`~zensols.amr.AmrDocument` instances."""

    token_index_mapper: Tuple[TokenIndexMapper] = field(default=None)
    """Adds token indicies to the AMR."""

    token_feature_populators: Tuple[TokenFeaturePopulator] = field(default=())
    """Populates the AMR graph with a feature."""

    doc_class: Type[AmrFeatureDocument] = field(default=AmrFeatureDocument)
    """The :class:`~zensols.nlp.FeatureDocument` class created to store
    :class:`zensols.amr.AmrDocument` instances.

    """
    sent_class: Type[AmrFeatureSentence] = field(default=AmrFeatureSentence)
    """The :class:`~zensols.nlp.FeatureSentence` class created to store
    :class:`zensols.amr.AmrSentence` instances.

    """
    def __post_init__(self):
        self.doc_class = AmrFeatureDocument
        self.sent_class = AmrFeatureSentence

    def _create_amr_doc(self, para: FeatureDocument) -> AmrDocument:
        doc = SpacyDocAdapter(para)
        self.amr_parser(doc)
        for sa, sd in zip(doc.sents, doc.sents):
            sa._.amr = sd._.amr
        if self.token_index_mapper is not None:
            self.token_index_mapper(doc)
        return doc._.amr

    def _create_amr_docs(self, paras: List[FeatureDocument]) -> \
            List[AmrDocument]:
        import itertools as it
        amr_docs: List[AmrDocument] = []
        para: FeatureDocument
        for para in it.islice(paras, 1):
            amr_docs.append(self._create_amr_doc(para))
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'returning {len(amr_docs)} paragraph documents')
        return amr_docs

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        key = f'{sec._row_id}-{sec.id}'
        paras: List[FeatureDocument] = super().__call__(sec)
        amr_paras: List[AmrFeatureDocument] = []
        if 1:
            self.sec_para_stash.clear()
        amr_docs: List[AmrDocument] = self.sec_para_stash.load(key)
        stash_miss = amr_docs is None
        if 1:
            paras = paras[:1]
            paras[0].sents = paras[0].sents[1:2]
        if amr_docs is None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'parsing {len(paras)}')
            amr_docs = self._create_amr_docs(paras)
        amr_doc: AmrDocument
        para: FeatureDocument
        for amr_doc, para in zip(amr_docs, paras):
            fsents: List[AmrFeatureSentence] = []
            for amr_sent, psent in zip(amr_doc.sents, para.sents):
                amr_fsent = psent.clone(self.sent_class, amr=amr_sent)
                fsents.append(amr_fsent)
            amr_fdoc = para.clone(self.doc_class, sents=fsents, amr=amr_doc)
            if stash_miss:
                for pop in self.token_feature_populators:
                    pop(amr_fdoc)
                self.sec_para_stash.dump(key, amr_docs)
            amr_paras.append(amr_fdoc)
        return amr_paras
