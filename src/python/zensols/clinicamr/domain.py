"""Object graph classes for EHR notes.

"""
__author__ = 'Paul Landes'

from typing import Tuple, List, Iterable
from dataclasses import dataclass, field
from abc import ABCMeta
import sys
from io import TextIOBase
from zensols.config import Writable
from zensols.util import APIError
from zensols.amr import AmrFeatureSentence, AmrFeatureDocument, AmrDocument


class ClinicAmrError(APIError):
    """Raised for this package's API errors."""
    pass


@dataclass
class _ParagraphIndex(object):
    span: Tuple[int, int] = field(default=None)


@dataclass
class _SectionIndex(object):
    id: int = field()
    name: str = field()
    paras: Tuple[_ParagraphIndex, ...] = field()

    @property
    def span(self) -> Tuple[int, int]:
        return (self.paras[0].span[0], self.paras[-1].span[1])


@dataclass
class _NoteIndex(object):
    row_id: int = field()
    secs: Tuple[_SectionIndex, ...] = field()

    @property
    def span(self) -> Tuple[int, int]:
        return (self.secs[0][0], self.secs[-1][1])


class _IndexedDocument(Writable, metaclass=ABCMeta):
    def __init__(self, sents: Tuple[AmrFeatureSentence]):
        self._sents = sents

    def _create_doc(self, index) -> AmrFeatureDocument:
        span: Tuple[int, int] = index.span
        sents: List[AmrFeatureSentence] = self._sents[span[0]:span[1]]
        return AmrFeatureDocument(
            sents=tuple(sents),
            amr=AmrDocument(tuple(map(lambda s: s.amr, sents))))

    def __getstate__(self):
        raise ClinicAmrError('Iinstances are not pickleable')


class SectionDocument(_IndexedDocument):
    def __init__(self, sents: Tuple[AmrFeatureSentence], sec_ix: _SectionIndex):
        super().__init__(sents)
        self._sec_ix = sec_ix

    def get_paragraphs(self) -> Iterable[AmrFeatureDocument]:
        return map(self._create_doc, self._sec_ix.paras)

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'section {self._sec_ix.id} ({self._sec_ix.name}):',
                         depth, writer)
        self._write_line('paragraphs:', depth, writer)
        para: AmrFeatureDocument
        for para in self.get_paragraphs():
            para.write(depth + 1, writer, include_amr=False,
                       include_normalized=False,
                       sent_kwargs=dict(include_amr=False))


class NoteDocument(_IndexedDocument):
    def __init__(self, sents: Tuple[AmrFeatureSentence], note_ix: _NoteIndex):
        super().__init__(sents)
        self._note_ix = note_ix

    def get_sections(self) -> Iterable[SectionDocument]:
        return map(lambda sec: SectionDocument(self._sents, sec),
                   self._note_ix.secs)

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'note: {self._note_ix.row_id}', depth, writer)
        self._write_line('sections:', depth, writer)
        sec: SectionDocument
        for sec in self.get_sections():
            self._write_object(sec, depth + 1, writer)


@dataclass
class AdmissionAmrFeatureDocument(AmrFeatureDocument):
    hadm_id: str = field(default=None)
    _note_ixs: Tuple[_NoteIndex, ...] = field(default=None)

    def get_notes(self) -> Iterable[SectionDocument]:
        return map(lambda note_ix: NoteDocument(self.sents, note_ix),
                   self._note_ixs)

    def write(self, depth: int = 0, writer: TextIOBase = sys.stdout):
        self._write_line(f'hadm: {self.hadm_id}', depth, writer)
        self._write_line('notes:', depth, writer)
        for note in self.get_notes():
            self._write_object(note, depth + 1, writer)
