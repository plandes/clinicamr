"""Adapt the :mod:`zensols.amrspring` client to a
:class:`zensols.amr.model.AmrParser`.

"""
__author__ = 'Paul Landes'

from typing import Tuple, Iterable
from dataclasses import dataclass, field
from spacy.tokens import Span
from zensols.nlp import FeatureDocument, FeatureDocumentParser
from zensols.amr import AmrFailure, AmrSentence
from zensols.amr.model import AmrParser
from zensols.amrspring import AmrPrediction, AmrParseClient


@dataclass
class SpringAmrParser(AmrParser):
    client: AmrParseClient = field(default=None)
    doc_parser: FeatureDocumentParser = field(default=None)

    def _parse_sents(self, sents: Iterable[Span]) -> Iterable[AmrSentence]:
        def map_mimic(sent: Span) -> str:
            """Remove MIMIC masks as they result in ``<pointer:0>`` type tokens
            from the SPRING parser.

            """
            doc: FeatureDocument = self.doc_parser(sent.text)
            return doc.norm

        sent_strs: Tuple[str] = tuple(map(map_mimic, sents))
        pred: AmrPrediction
        for pred in self.client.parse(sent_strs):
            if pred.is_error:
                fail = AmrFailure(message=pred.error, sent=pred.sent)
                yield AmrSentence(fail)
            else:
                yield AmrSentence(pred.graph, model=self.model)
