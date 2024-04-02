"""Parse clinical medical note paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import Sequence, Iterable
from dataclasses import dataclass, field
import logging
from zensols.persist import Stash
from zensols.nlp import FeatureDocument, FeatureDocumentDecorator
from zensols.amr import AmrError, AmrFeatureDocument
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
    def _get_doc(self, pid: str, para: FeatureDocument) -> AmrFeatureDocument:
        fdoc: AmrFeatureDocument = self.stash.load(pid)
        if fdoc is None:
            fdoc = self.amr_annotator.annotate(para)
            dec: FeatureDocumentDecorator
            for dec in self.document_decorators:
                dec.decorate(fdoc)
            self.stash.dump(pid, fdoc)
        return fdoc

    def create(self, sec: Section) -> Iterable[FeatureDocument]:
        nid: int = sec.container.row_id
        paras: Iterable[FeatureDocument] = self.delegate.create(sec)
        para: FeatureDocument
        for pix, para in enumerate(paras):
            try:
                doc = self._get_doc(f'{nid}-{sec.id}-{pix}', para)
            except Exception as e:
                raise AmrError(f'Could not parse AMR for <{para.text}>') from e
            yield doc

    def clear(self):
        self.stash.clear()
