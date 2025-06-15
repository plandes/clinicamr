"""Adds concept unique identifiers to the graph.

"""
__author__ = 'Paul Landes'

from typing import List
from dataclasses import dataclass, field
from penman.graph import Graph, Triple, Attribute
from zensols.nlp import FeatureToken
from zensols.amr.docparser import TokenAnnotationFeatureDocumentDecorator


@dataclass
class ClinicTokenAnnotationFeatureDocumentDecorator(
        TokenAnnotationFeatureDocumentDecorator):
    """Override token feature annotation by adding CUI data.

    """
    feature_format: str = field(default='{pref_name_} ({cui_})')
    """The format used for CUI annotated tokens."""

    def _format_feature_value(self, tok: FeatureToken) -> str:
        if tok.is_concept and self.feature_format is not None:
            return self.feature_format.format(**tok.asdict())
        return getattr(tok, self.feature_id)

    def _annotate_token(self, tok: FeatureToken, source: Triple,
                        feature_triples: List[Attribute], graph: Graph):
        # when we find a concept, add in the CUI if the token is a
        # concept
        if tok.is_concept and tok.cui_ != FeatureToken.NONE:
            super()._annotate_token(tok, source, feature_triples, graph)
