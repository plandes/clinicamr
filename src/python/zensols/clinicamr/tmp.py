"""Clinet usage.

"""
__author__ = 'Paul Landes'

from typing import Dict, Any
from dataclasses import dataclass, field
from zensols.mimic import NoteEvent, Note, NoteFactory


@dataclass
class DecoratorNoteFactory(NoteFactory):
    category_to_note: Dict[str, str] = field(default=None)
    """Unused."""

    mimic_default_note_section: str = field(default=None)
    """Unused."""

    delegate: NoteFactory = field(default=None)

    def _event_to_note(self, note_event: NoteEvent, section: str,
                       params: Dict[str, Any] = None) -> Note:
        return self.delegate(note_event, section, params)

    def _create_from_note_event(self, note_event: NoteEvent,
                                section: str = None) -> Note:
        return self.delegate(note_event, section)

    def create(self, note_event: NoteEvent) -> Note:
        return self._create_from_note_event(note_event, None)

    def create_default(self, note_event: NoteEvent) -> Note:
        return self.delegate.create_default(note_event)

    def prime(self):
        self.delegate.prime()
