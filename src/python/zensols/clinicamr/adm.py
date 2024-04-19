"""Classes used to parse the clinical corpus into an annotated AMR corpus.

"""
__author__ = 'Paul Landes'

from typing import List, Tuple, Dict, Set, Iterable, Union
from dataclasses import dataclass, field
from zensols.persist import Stash, ReadOnlyStash
from zensols.mimic import MimicError, Section, Note, HospitalAdmission
from zensols.mimic import Corpus as MimicCorpus
from zensols.mimic.regexnote import DischargeSummaryNote
from zensols.amr import (
    AmrFeatureSentence, AmrFeatureDocument, AmrSentence, AmrDocument
)
from .domain import (
    _ParagraphIndex, _SectionIndex, _NoteIndex, ParseFailure,
    AdmissionAmrFeatureDocument
)


@dataclass
class AdmissionAmrFactoryStash(ReadOnlyStash):
    """A stash that CRUDs instances of :obj:`.AdmissionAmrFeatureDocument`.

    """
    mimic_corpus: MimicCorpus = field()
    """The MIMIC-III corpus."""

    filter_summary_sections: Union[List[str], Set[str]] = field()
    """The sections to keep in each clinical note.  The rest are filtered."""

    def __post_init__(self):
        super().__post_init__()
        if not isinstance(self.filter_summary_sections, set):
            self.filter_summary_sections = set(self.filter_summary_sections)

    def _load_note(self, note: Note, include_sections: Set[str],
                   sents: List[AmrFeatureSentence],
                   fails: List[ParseFailure]) -> _NoteIndex:
        """Index a note and track its sentences as section and paragraph levels.

        :param note: the note to create

        :param include_sections: the sections in the note to keep

        :param sents: the list to populate with paragraph level sentences

        :param fails: a list of sentences with a failed AMR parse

        :return: a note, section and paragraph level index

        """
        sec_ixs: List[_SectionIndex] = []
        secs: Iterable[Section] = note.sections.values()
        if include_sections is not None:
            secs = filter(lambda s: s.name in include_sections, secs)
        # iterate through sections and tracking their indexes
        sec: Section
        for sec in secs:
            para_ixs: List[_ParagraphIndex] = []
            # iterate through each paragraph, track their indexes and sentences
            para: AmrFeatureDocument
            pix: int
            for pix, para in enumerate(sec.paragraphs):
                para_begin: int = len(sents)
                assert isinstance(para, AmrFeatureDocument)
                assert isinstance(para.amr, AmrDocument)
                # each sentence is added to be retrieved in domain class indexes
                sent: AmrFeatureSentence
                for sent in para:
                    assert isinstance(sent, AmrFeatureSentence)
                    assert isinstance(sent.amr, AmrSentence)
                    if sent.is_failure:
                        fails.append(ParseFailure(
                            row_id=note.row_id,
                            sec_id=sec.id,
                            sec_name=sec.name,
                            para_idx=pix,
                            sent=sent))
                    else:
                        sents.append(sent)
                para_ixs.append(_ParagraphIndex(span=(para_begin, len(sents))))
            sec_ixs.append(_SectionIndex(
                id=sec.id,
                name=sec.name.replace('-', ' '),
                paras=tuple(para_ixs)))
        return _NoteIndex(
            row_id=note.row_id,
            category=note.id.replace('-', ' '),
            secs=tuple(sec_ixs))

    def load(self, hadm_id: str) -> AdmissionAmrFeatureDocument:
        """Load an admission from the MIMIC-III package and parse it for
        language and AMRs.

        :param hadm_id: the MIMIC-III admission ID

        :return: the parsed admission

        """
        notes: List[_NoteIndex] = []
        sents: List[AmrFeatureSentence] = []
        fails: List[ParseFailure] = []
        stash: Stash = self.mimic_corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        ds_hadm_ids: Set[str] = set(map(lambda n: n.row_id, ds_notes))
        if len(ds_notes) == 0:
            raise MimicError(
                f'No discharge sumamries for admission: {adm.hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        ds_ix: _NoteIndex = self._load_note(
            ds_note, self.filter_summary_sections, sents, fails)
        ant_notes: List[Note] = sorted(
            filter(lambda n: n.row_id not in ds_hadm_ids, adm.notes),
            key=lambda n: n.row_id)
        for note in ant_notes:
            notes.append(self._load_note(note, None, sents, fails))
        return AdmissionAmrFeatureDocument(
            sents=tuple(sents),
            amr=AmrDocument(tuple(map(lambda s: s.amr, sents))),
            hadm_id=adm.hadm_id,
            _ds_ix=ds_ix,
            _ant_ixs=tuple(notes),
            parse_fails=fails)

    def keys(self) -> Iterable[str]:
        return self.corpus.hospital_adm_stash.keys()

    def exists(self, hadm_id: str) -> bool:
        return self.corpus.hospital_adm_stash.exists(hadm_id)
