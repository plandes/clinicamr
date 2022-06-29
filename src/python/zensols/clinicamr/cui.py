"""
"""
__author__ = 'Paul Landes'

from typing import List, Tuple
from dataclasses import dataclass, field
import logging
from spacy.tokens import Doc
from penman.graph import Graph
from penman import constant
from zensols.nlp import (
    FeatureToken, FeatureSentence, FeatureDocument, SpacyFeatureDocumentParser
)
from zensols.amr import (
    AmrError, AmrParser, AmrSentence, AmrFeatureSentence, AmrFeatureDocument
)
from zensols.mimic import NoteEvent, Note, ParagraphFactory, Section
from zensols.mimicsid import AnnotationNoteFactory

logger = logging.getLogger(__name__)


@dataclass
class ClinicAmrParagraphFactory(ParagraphFactory):
    amr_parser: AmrParser = field()
    doc_parser: SpacyFeatureDocumentParser = field()

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        paras = super().__call__(sec)
        amr_paras: List[FeatureDocument] = []
        para: FeatureDocument
        for para in paras:
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
            amr_paras.append(self.doc_parser.from_spacy_doc(doc))
            # for sent, span in zip(para, doc.sents):
            #     print(span._.amr.graph_string)
        for p in amr_paras:
            print('PAR', p)
        return amr_paras


# @dataclass
# class ClinicAmrAnnotationNoteFactory(AnnotationNoteFactory):
#     def __call__(self, note_event: NoteEvent) -> Note:
#         note: Note = super().__call__(note_event)
#         note.paragraph_factory = ClinicAmrParagraphFactory
#         return note


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
