"""Parse paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List, Tuple
from dataclasses import dataclass, field
import logging
from spacy.tokens import Doc
from penman.graph import Graph
from penman import constant
from zensols.persist import Stash
from zensols.nlp import (
    FeatureToken, FeatureSentence, FeatureDocument, SpacyFeatureDocumentParser
)
from zensols.amr import (
    AmrError, AmrParser, AmrDocument, AmrSentence,
    AmrFeatureSentence, AmrFeatureDocument,
)
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
    amr_parser: AmrParser = field()
    """The AMR parser used to induce the graphs."""

    doc_parser: SpacyFeatureDocumentParser = field()
    """The parser used to convert super class (see class docs) documents back in
    spaCy :class:`~spacy.tokens.Doc` instances.

    """
    sec_para_stash: Stash = field()
    """Used to store the :class:`~zensols.amr.AmrDocument` instances."""

    def _create_amr_doc(self, para: FeatureDocument) -> AmrDocument:
        # (at least) gsii models can't handle tokens with spaces, which happens
        # in multi-word entries, so chop them
        #
        # TODO: add a whitespace split token normalizer
        for t in para.token_iter():
            pos = t.norm.find(' ')
            if pos > -1:
                t.norm = t.norm[:pos]
        # create a spacy doc from our feature document
        doc: Doc = self.doc_parser.to_spacy_doc(
            para, add_features=set('pos tag lemma ent'.split()))
        for t in doc:
            # the token normalization process splits on newlines, but the
            # new lines also pop up in the lemmas
            if t.lemma_.find('\n') > -1:
                t.lemma_ = t.orth_
            else:
                pos = t.lemma_.find(' ')
                if pos > -1:
                    t.lemma_ = t.lemma_[:pos]
        self.amr_parser(doc)
        return doc._.amr

    def _create_amr_docs(self, paras: List[FeatureDocument]) -> \
            List[AmrDocument]:
        amr_docs: List[AmrDocument] = []
        para: FeatureDocument
        for para in paras:
            amr_docs.append(self._create_amr_doc(para))
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'returning {len(amr_docs)} paragraph documents')
        return amr_docs

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        key = f'{sec._row_id}-{sec.id}'
        paras: List[FeatureDocument] = super().__call__(sec)
        amr_paras: List[AmrFeatureDocument] = []
        amr_docs: List[AmrDocument] = self.sec_para_stash.load(key)
        if amr_docs is None:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'parsing {len(paras)}')
            amr_docs = self._create_amr_docs(paras)
            self.sec_para_stash.dump(key, amr_docs)
        amr_doc: AmrDocument
        para: FeatureDocument
        for amr_doc, para in zip(amr_docs, paras):
            fsents: List[AmrFeatureSentence] = []
            for amr_sent, psent in zip(amr_doc.sents, para.sents):
                amr_fsent = psent.clone(AmrFeatureSentence, amr=amr_sent)
                fsents.append(amr_fsent)
            amr_fdoc = para.clone(AmrFeatureDocument, amr=amr_doc)
            amr_paras.append(amr_fdoc)
        return amr_paras


@dataclass
class CuiAmrFeatureSentence(AmrFeatureSentence):
    token_index_role: str = field(default='toki')
    cui_role: str = field(default='cui')
    cui_attribute: str = field(default='cui_')

    def _populate_cuis(self):
        amr: AmrSentence = self.amr
        graph: Graph = amr.graph
        cuis: List[Tuple[str, str, str]] = []
        tirs: List[int] = []
        # find triples that identify token index positions
        for ax, src_trip in enumerate(graph.triples):
            source, rel, target = src_trip
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'triple: {src_trip}')
            # match on role name
            if rel.startswith(self.token_index_role):
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'found relation: {rel}, target: {target}')
                # list indexes are comma separated
                for ix in map(int, constant.evaluate(target).split(',')):
                    td: FeatureToken = self.tokens_by_idx[ix]
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f'token: {ix} -> {td}')
                    # when we find a concept, add in the CUI if the token is a
                    # concept
                    if td.is_concept:
                        triple = (source, self.cui_role,
                                  getattr(td, self.cui_attribute))
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f'adding: {triple}')
                            logger.debug(f'to rm: {src_trip} at index={ax}')
                        # add the CUI as a triple to graph
                        cuis.append(triple)
                    # remove the token index relation later
                    tirs.append(ax)
        tirs = sorted(set(tirs), reverse=True)
        for ax in tirs:
            del graph.triples[ax]
        graph.triples.extend(cuis)
        self.amr = AmrSentence(graph)


@dataclass
class CuiAmrFeatureDocument(AmrFeatureDocument):
    def __post_init__(self):
        super().__post_init__()
        fs: FeatureSentence
        for fs in self.sents:
            if not isinstance(fs.amr, AmrError):
                fs._populate_cuis()
