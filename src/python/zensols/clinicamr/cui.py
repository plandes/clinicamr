from __future__ import annotations
"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List, Tuple, Type, Set, Any
from dataclasses import dataclass, field
import logging
from penman.graph import Graph
from penman import constant
from zensols.persist import Stash
from zensols.nlp import (
    FeatureToken, FeatureDocument, SpacyFeatureDocumentParser
)
from zensols.amr import (
    AmrParser, AmrDocument, AmrSentence,
    AmrFeatureSentence, AmrFeatureDocument, TokenIndexMapper,
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


@dataclass
class TokenFeaturePopulator(object):
    """Populate features in AMR sentence graphs from indexes populated from
    :class:`.TokenIndexMapper`.

    """
    role: str = field()
    """The triple role used to label the edge between the token and the feature.

    """
    feature_id: str = field()
    """The :class:`~zensols.nlp.FeatureToken` ID (attribute) to populate in the
    AMR graph.

    """
    token_index_role: str = field(
        default=TokenIndexMapper.DEFAULT_TOKEN_INDEX_ROLE)
    """The token index role (edge) that has the token index, which is token
    character offset added by :class:`.TokenIndexMapper`.

    """
    remove_indexes: bool = field(default=True)
    """Whether to remove the :obj:`token_index_role` edges after processing."""

    def __call__(self, doc: AmrFeatureDocument):
        updates: List[AmrSentence] = []
        sent: AmrSentence
        for sent in doc.sents:
            updates.append(self._populate_sentence(sent, doc))
        doc.amr.sents = updates

    def _populate_sentence(self, sent: AmrFeatureSentence,
                           doc: AmrFeatureDocument):
        token_index_role = self.token_index_role
        tokens_by_idx = doc.tokens_by_idx
        graph: Graph = sent.amr.graph
        feat_trips: Set[Tuple[str, str, str]] = set()
        trip_remove_ixs: List[int] = []
        # find triples that identify token index positions
        tix: int
        src_trip: Tuple[str, str, Any]
        for tix, src_trip in enumerate(graph.triples):
            source, rel, target = src_trip
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'triple: {src_trip}')
            # match on role name
            if rel.startswith(token_index_role):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'found relation: {rel}, target: {target}')
                # list indexes are comma separated
                for ix in map(int, constant.evaluate(target).split(',')):
                    td: FeatureToken = tokens_by_idx[ix]
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f'token: {ix} -> {td}')
                    # when we find a concept, add in the CUI if the token is a
                    # concept
                    if td.is_concept:
                        val = constant.quote(getattr(td, self.feature_id))
                        triple = (source, self.role, val)
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f'adding: {triple}')
                            logger.debug(f'to rm: {src_trip} at index={tix}')
                        # add the faeture as a triple to graph
                        feat_trips.add(triple)
                    # remove the token index relation later
                    trip_remove_ixs.append(tix)
        if self.remove_indexes:
            trip_remove_ixs = sorted(set(trip_remove_ixs), reverse=True)
            for tix in trip_remove_ixs:
                del graph.triples[tix]
        graph.triples.extend(feat_trips)
        return AmrSentence(graph)
