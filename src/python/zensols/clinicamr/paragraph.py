"""Parse clinical medical note paragraph AMR graphs and cache using a
:class:`~zensols.persist.Stash`.

"""
__author__ = 'Paul Landes'

from typing import List
from dataclasses import dataclass, field
import sys
import logging
from pathlib import Path
import itertools as it
from zensols.nlp import FeatureDocument, FeatureDocumentParser
from zensols.amr import AmrFeatureDocument, AmrDocument
from zensols.mimic import ParagraphFactory, Section, MimicTokenDecorator

logger = logging.getLogger(__name__)


@dataclass
class ClinicAmrDocument(AmrDocument):
    """An AMR document with a sub pat used when generating diagram plots.

    :see: :class:`.ClinicAmrParagraphFactory`

    """
    sub_path: Path = field(default=None)

    def _get_plot_dir(self, base_path: Path) -> Path:
        if self.sub_path is None:
            return base_path
        else:
            return base_path / self.sub_path


@dataclass
class ClinicAmrParagraphFactory(ParagraphFactory):
    """Parse paragraph AMR graphs by using the super class paragraph factory.
    Then each document is given an AMR graph using a
    :class:`~zensols.amr.AmrDocument` at the document level and a
    :class:`~zensols.amr.AmrSentence` at the sentence level, which are are
    cached using a :class:`~zensols.persist.Stash`.

    A list of :class:`~zensols.amr.AmrFeatureDocument` are returned.

    """
    doc_parser: FeatureDocumentParser = field()
    """Parses, populates and caches AMR graphs in feature documents."""

    limit: int = field(default=sys.maxsize)
    """Limit on number of paragraphs to process and useful for prototyping."""

    def _fix_lemmas(self, doc: FeatureDocument):
        """Assume this document has been unpersisted from the file system so
        modify in place.

        """
        for tok in doc.token_iter():
            mimic_tok_feat = getattr(tok, MimicTokenDecorator.TOKEN_FEATURE_ID)
            if mimic_tok_feat == MimicTokenDecorator.PSEUDO_TOKEN_FEATURE:
                tok.lemma_ = tok.norm

    def __call__(self, sec: Section) -> List[FeatureDocument]:
        paras: List[FeatureDocument] = super().__call__(sec)
        amr_paras: List[AmrFeatureDocument] = []
        para: FeatureDocument
        for pix, para in enumerate(it.islice(paras, self.limit)):
            sub_path = Path(f'{sec.id}-{pix}')
            self._fix_lemmas(para)
            amr_fdoc: AmrFeatureDocument = self.amr_annotator(para)
            ad: AmrDocument = amr_fdoc.amr
            amr_fdoc.amr = ClinicAmrDocument(ad.sents, ad.path, sub_path)
            amr_paras.append(amr_fdoc)
        return amr_paras
