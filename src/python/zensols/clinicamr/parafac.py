"""Parse clinical medical note paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import Dict, Tuple, Sequence, Iterable
from dataclasses import dataclass, field
import logging
from zensols.persist import Stash
from zensols.nlp import LexicalSpan, FeatureDocument, FeatureDocumentDecorator
from zensols.amr import (
    AmrError, AmrSentence, AmrFeatureSentence, AmrFeatureDocument
)
from zensols.amr.annotate import AnnotationFeatureDocumentParser
from zensols.mimic import ParagraphFactory, Section

logger = logging.getLogger(__name__)


@dataclass
class ClinicAmrParagraphFactory(ParagraphFactory):
    """Parse paragraph AMR graphs by using the super class paragraph factory.
    Then each document is given an AMR graph using a
    :class:`~zensols.amr.doc.AmrDocument` at the document level and a
    :class:`~zensols.amr.sent.AmrSentence` at the sentence level, which are
    cached using a :class:`~zensols.persist.Stash`.

    A list of :class:`~zensols.amr.doc.AmrFeatureDocument` are returned.

    """
    delegate: ParagraphFactory = field()
    """The paragraph factory that chunks the paragraphs."""

    amr_annotator: AnnotationFeatureDocumentParser = field()
    """Parses, populates and caches AMR graphs in feature documents."""

    stash: Stash = field()
    """Caches full paragraph :class:`~zensols.amr.doc.AmrFeatureDocument`
    instances.

    """
    document_decorators: Sequence[FeatureDocumentDecorator] = field(
        default=())
    """A list of decorators that can add, remove or modify features on a
    document.

    """
    add_id: bool = field(default=True)
    """Whether to add the ``id`` AMR metadata field if it does not already
    exist.

    """
    add_is_header: bool = field(default=True)
    """Whether or not to add the ``is_header`` AMR metadata indicating if the
    sentence is part of one of the section headers.

    """
    def _add_id(self, pid: str, doc: AmrFeatureDocument):
        did: str = 'MIMIC3_' + pid.replace('-', '_')
        sent: AmrSentence
        for sid, sent in enumerate(doc.amr.sents):
            meta: Dict[str, str] = sent.metadata
            if 'id' not in meta:
                meta['id'] = f'{did}.{sid}'
            sent.metadata = meta

    def _add_is_header(self, sec: Section, sent: AmrFeatureSentence):
        hspans: Tuple[LexicalSpan, ...] = ()
        if len(sec.header_spans) > 0:
            off: int = sec.header_spans[0].begin
            hspans = tuple(map(
                lambda hs: LexicalSpan(off - hs[0], off - hs[1]),
                sec.header_spans))
        is_header: bool = any(map(
            lambda hs: sent.lexspan.overlaps_with(hs), hspans))
        sent.amr.set_metadata('is_header', 'true' if is_header else 'false')

    def _get_doc(self, pid: str, sec: Section, para: FeatureDocument) -> \
            AmrFeatureDocument:
        fdoc: AmrFeatureDocument = self.stash.load(pid)
        if fdoc is None:
            fdoc = self.amr_annotator.annotate(para)
            dec: FeatureDocumentDecorator
            for dec in self.document_decorators:
                dec.decorate(fdoc)
            if self.add_id:
                self._add_id(pid, fdoc)
            if self.add_is_header:
                for s in fdoc:
                    self._add_is_header(sec, s)
            self.stash.dump(pid, fdoc)
        return fdoc

    def create(self, sec: Section) -> Iterable[FeatureDocument]:
        nid: int = sec.container.row_id
        paras: Iterable[FeatureDocument] = self.delegate.create(sec)
        para: FeatureDocument
        for pix, para in enumerate(paras):
            try:
                doc = self._get_doc(f'{nid}-{sec.id}-{pix}', sec, para)
            except Exception as e:
                raise AmrError(f'Could not parse AMR for <{para.text}>') from e
            yield doc

    def clear(self):
        self.stash.clear()
