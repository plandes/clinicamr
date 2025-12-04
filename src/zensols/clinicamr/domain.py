"""Object graph classes for EHR notes.

"""
__author__ = 'Paul Landes'

from typing import Tuple, List, Iterable, Type
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod
import sys
import copy
from io import TextIOBase
from zensols.config import Writable
from zensols.persist import NotPickleable
from zensols.util import APIError
from zensols.nlp import TokenContainer
from zensols.amr import AmrFeatureSentence, AmrFeatureDocument, AmrDocument


class ClinicAmrError(APIError):
    """Raised for this package's API errors."""
    pass


@dataclass
class _ParagraphIndex(object):
    """A paragraph index as a span of sentence entries in
    :class:`._IndexedDocument`.

    """
    span: Tuple[int, int] = field(default=None)
    """The 0-index sentence beginning and inclusive ending that make up the
    paragraph."""


@dataclass
class _SectionIndex(object):
    """A section made up of paragraph sentence spans.

    """
    id: int = field()
    """The :obj:`~zensols.mimic.note.Section.id`."""

    name: str = field()
    """The :obj:`~zensols.mimic.note.Section.name`."""

    paras: Tuple[_ParagraphIndex, ...] = field()
    """Paragraph sentence spans."""

    @property
    def span(self) -> Tuple[int, int]:
        """The 0-index sentence beginning and inclusive ending that make up the
        section.

        """
        return (self.paras[0].span[0], self.paras[-1].span[1])


@dataclass
class _NoteIndex(object):
    """The sections that make up a note.

    """
    row_id: int = field()
    """The MIMIC-III unique row ID of the clinical note."""

    category: str = field()
    """The category of the note (i.e. ``discharge-summary``)."""

    secs: Tuple[_SectionIndex, ...] = field()
    """The section indexes the make up the note."""

    @property
    def span(self) -> Tuple[int, int]:
        """The 0-index sentence beginning and inclusive ending that make up the
        clinical note.

        """
        return (self.secs[0].paras[0].span[0], self.secs[-1].paras[-1].span[1])


class _IndexedDocument(Writable, NotPickleable, metaclass=ABCMeta):
    """A base class for index container classes that create AMR documents.

    """
    def __init__(self, sents: Tuple[AmrFeatureSentence]):
        self._sents = sents

    @abstractmethod
    def create_document(self) -> AmrFeatureDocument:
        """Create an AMR feature document."""
        pass

    def _create_doc(self, index) -> AmrFeatureDocument:
        """Create a paragraph document from a :class:`._NoteIndex` or like
        (``_*Index``) object.

        """
        span: Tuple[int, int] = index.span
        sents: List[AmrFeatureSentence] = self._sents[span[0]:span[1]]
        return AmrFeatureDocument(
            sents=tuple(sents),
            amr=AmrDocument(tuple(map(lambda s: s.amr, sents))))


@dataclass
class ParseFailure(Writable):
    """A container class for sentences who have parsed features, but the AMR
    parse failed.

    """
    row_id: int = field()
    """The MIMIC-III unique row ID of the clinical note."""

    sec_id: int = field()
    """The :obj:`~zensols.mimic.note.Section.id`."""

    sec_name: str = field()
    """The :obj:`~zensols.mimic.note.Section.name`."""

    para_idx: int = field()
    """The index of the paragraph."""

    sent: AmrFeatureSentence = field()
    """The AMR sentence.

    :see: :obj:`~zensols.amr.container.AmrFeatureSentence.is_failure`

    """
    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'note={self.row_id}, ' +
                         f'section={self.sec_name} ({self.sec_id}), ' +
                         f'paragraph={self.para_idx}:', depth, writer)
        self._write_block(self.sent.text, depth + 1, writer)


class SectionDocument(_IndexedDocument):
    """An index container class that creates AMR paragraph documents.

    """
    def __init__(self, sents: Tuple[AmrFeatureSentence], sec_ix: _SectionIndex):
        super().__init__(sents)
        self._sec_ix = sec_ix

    @property
    def id(self) -> int:
        """The :obj:`~zensols.mimic.note.Section.id`."""
        return self._sec_ix.id

    @property
    def name(self) -> str:
        """The :obj:`~zensols.mimic.note.Section.name`."""
        return self._sec_ix.name

    def create_paragraphs(self) -> Iterable[AmrFeatureDocument]:
        """Return the paragraph documents of this section."""
        return map(self._create_doc, self._sec_ix.paras)

    def create_document(self) -> AmrFeatureDocument:
        return self._create_doc(self._sec_ix)

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'section {self.id} ({self.name}):', depth, writer)
        self._write_line('paragraphs:', depth, writer)
        para: AmrFeatureDocument
        for para in self.create_paragraphs():
            para.write(depth + 1, writer, include_amr=False,
                       include_normalized=False,
                       sent_kwargs=dict(include_amr=False))


class NoteDocument(_IndexedDocument):
    """An index container class that creates AMR clinical note documents.

    """
    def __init__(self, sents: Tuple[AmrFeatureSentence], note_ix: _NoteIndex):
        super().__init__(sents)
        self._note_ix = note_ix

    @property
    def row_id(self) -> int:
        """The MIMIC-III unique row ID of the clinical note."""
        return self._note_ix.row_id

    @property
    def category(self) -> str:
        """The category of the note (i.e. ``discharge-summary``)."""
        return self._note_ix.category

    def create_document(self) -> AmrFeatureDocument:
        return self._create_doc(self._note_ix)

    def create_sections(self) -> Iterable[SectionDocument]:
        """Return the clinical section documents of this section."""
        return map(lambda sec: SectionDocument(self._sents, sec),
                   self._note_ix.secs)

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'note: {self.row_id} ({self.category})',
                         depth, writer)
        self._write_line('sections:', depth, writer)
        sec: SectionDocument
        for sec in self.create_sections():
            self._write_object(sec, depth + 1, writer)


@dataclass
class AdmissionAmrFeatureDocument(AmrFeatureDocument):
    """An AMR feature document whose :obj:`sents` consist of all parsed
    sentences of all notes of an admission.

    """
    hadm_id: str = field(default=None)
    """The MIMIC-III admission ID."""

    _ds_ix: _NoteIndex = field(default=None)
    """The discharge summary index."""

    _ant_ixs: Tuple[_NoteIndex, ...] = field(default=None)
    """The note antecedent indexes."""

    parse_fails: Tuple[ParseFailure, ...] = field(default=None)
    """Sentences who have parsed features, but the AMR parse failed."""

    def create_discharge_summary(self) -> NoteDocument:
        """Return the discharge summary note."""
        return NoteDocument(self.sents, self._ds_ix)

    def create_note_antecedents(self) -> Iterable[NoteDocument]:
        """Return the clinical notes of the admission."""
        return map(lambda note_ix: NoteDocument(self.sents, note_ix),
                   self._ant_ixs)

    def clone(self, cls: Type[TokenContainer] = None, **kwargs) -> \
            TokenContainer:
        clone = super().clone(cls, **kwargs)
        clone._ds_ix = copy.deepcopy(self._ds_ix)
        clone._ant_ixs = copy.deepcopy(self._ant_ixs)
        clone.parse_fails = copy.deepcopy(self.parse_fails)
        return clone

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'hadm: {self.hadm_id}', depth, writer)
        self._write_line('summary:', depth, writer)
        self._write_object(self.create_discharge_summary(), depth + 1, writer)
        self._write_line('antecedents:', depth, writer)
        for note in self.create_note_antecedents():
            self._write_object(note, depth + 1, writer)
