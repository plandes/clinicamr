"""Parse clinical medical note paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import Dict, Tuple, Sequence, Iterable
from dataclasses import dataclass, field
import logging
from zensols.persist import Stash
from zensols.nlp import (
    LexicalSpan, FeatureSentence, FeatureDocument, FeatureDocumentDecorator,
    FeatureSentenceDecorator
)
from zensols.amr import AmrSentence, AmrFeatureSentence, AmrFeatureDocument
from zensols.amr.annotate import AnnotationFeatureDocumentParser
from zensols.mimic import ParagraphFactory, Section

logger = logging.getLogger(__name__)


@dataclass
class ClinicAmrParagraphFactory(ParagraphFactory):
    """Parse paragraph AMR graphs by using the the :obj:`delegate` paragraph
    factory.  Then each document is given an AMR graph using a
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
    sentence_decorators: Sequence[FeatureSentenceDecorator] = field(
        default=())
    """A list of decorators that can add, remove or modify features on a
    document.

    """
    id_format: str = field(
        default='MIMIC3_{note_id}_{sec_id}_{para_id}.{sent_id}')
    """Whether to add the ``id`` AMR metadata field if it does not already
    exist.

    """
    add_is_header: bool = field(default=True)
    """Whether or not to add the ``is_header`` AMR metadata indicating if the
    sentence is part of one of the section headers.

    """
    remove_empty_sentences: bool = field(default=True)
    """Whether to remove empty sentences from paragraphs. If ``True`` empty
    paragraphs are skipped.

    """
    def __post_init__(self):
        Section.FILTER_ENUMS = False

    def _add_id(self, nid: int, sec: Section, pix: int,
                doc: AmrFeatureDocument):
        sent: AmrSentence
        for six, sent in enumerate(doc.amr.sents):
            meta: Dict[str, str] = sent.metadata
            if 'id' not in meta:
                meta['id'] = self.id_format.format(
                    note_id=nid,
                    sec_id=sec.id,
                    sec_name=sec.name,
                    para_id=pix,
                    sent_id=six)
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

    def _get_doc(self, sec: Section, pix: int, para: FeatureDocument) -> \
            AmrFeatureDocument:
        nid: int = sec.container.row_id
        pid: str = f'{nid}-{sec.id}-{pix}'
        fdoc: AmrFeatureDocument = self.stash.load(pid)
        if fdoc is None:
            cr = self.amr_annotator.coref_resolver
            self.amr_annotator.coref_resolver = None
            try:
                fdoc = self.amr_annotator.annotate(para)
            finally:
                self.amr_annotator.coref_resolver = cr
            sdec: FeatureSentenceDecorator
            for sdec in self.sentence_decorators:
                sent: FeatureSentence
                for sent in fdoc.sents:
                    sdec.decorate(sent)
            dec: FeatureDocumentDecorator
            for dec in self.document_decorators:
                dec.decorate(fdoc)
            if self.id_format is not None:
                self._add_id(nid, sec, pix, fdoc)
            if self.add_is_header:
                for s in fdoc:
                    self._add_is_header(sec, s)
            self.stash.dump(pid, fdoc)
        return fdoc

    def create(self, sec: Section) -> Iterable[FeatureDocument]:
        paras: Iterable[FeatureDocument] = self.delegate.create(sec)
        para: FeatureDocument
        for pix, para in enumerate(paras):
            if self.remove_empty_sentences:
                para.sents = tuple(filter(
                    lambda s: len(s.norm.strip()) > 0,
                    para.sents))
            if len(para.sents) == 0:
                continue
            doc: FeatureDocument = None
            try:
                doc = self._get_doc(sec, pix, para)
            except Exception as e:
                msg: str = f'Could not parse AMR for <{para.text}>: {e}'
                logging.exception(msg)
            if doc is not None:
                yield doc

    def clear(self):
        self.stash.clear()
