"""Adds concept unique identifiers to the graph.

"""
__author__ = 'Paul Landes'

from typing import Set, Tuple
from dataclasses import dataclass
from penman import Graph
from zensols.nlp import FeatureToken
from zensols.amr import TokenAnnotationFeatureDocumentDecorator


@dataclass
class ClinicTokenAnnotationFeatureDocumentDecorator(
        TokenAnnotationFeatureDocumentDecorator):
    """Override token feature annotation by adding CUI data.

    """
    def _format_feature_value(self, tok: FeatureToken) -> str:
        return f'{tok.pref_name_} ({tok.cui_})'
        return getattr(tok, self.feature_id)

    def _annotate_token(self, tok: FeatureToken, source: str,
                        feature_triples: Set[Tuple[str, str, str]],
                        graph: Graph):
        # when we find a concept, add in the CUI if the token is a
        # concept
        if tok.is_concept:
            super()._annotate_token(tok, source, feature_triples, graph)
