"""
"""
__author__ = 'Paul Landes'

from typing import List, Tuple
from dataclasses import dataclass, field
import logging
from penman.graph import Graph
from penman import constant
from zensols.nlp import FeatureToken, FeatureSentence
from zensols.amr import (
    AmrError, AmrSentence, AmrFeatureSentence, AmrFeatureDocument
)

logger = logging.getLogger(__name__)


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
