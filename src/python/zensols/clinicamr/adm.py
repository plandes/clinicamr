"""Classes used to parse the clinical corpus into an annotated AMR corpus.

"""
__author__ = 'Paul Landes'

from typing import List, Dict, Set, Iterable, Union
from dataclasses import dataclass, field
import logging
from zensols.persist import ReadOnlyStash
from zensols.mimic import MimicError, Section, Note, HospitalAdmission
from zensols.mimic import Corpus as MimicCorpus
from zensols.mimic.regexnote import DischargeSummaryNote
from zensols.amr import (
    AmrFeatureSentence, AmrFeatureDocument, AmrSentence, AmrDocument
)
from zensols.amr.annotate import AnnotationFeatureDocumentParser
from .domain import (
    _ParagraphIndex, _SectionIndex, _NoteIndex, ParseFailure,
    AdmissionAmrFeatureDocument
)

logger = logging.getLogger(__name__)


@dataclass
class AdmissionAmrFactoryStash(ReadOnlyStash):
    """A stash that CRUDs instances of :obj:`.AdmissionAmrFeatureDocument`.

    """
    corpus: MimicCorpus = field()
    """The MIMIC-III corpus."""

    amr_annotator: AnnotationFeatureDocumentParser = field()
    """Parses, populates and caches AMR graphs in feature documents."""

    keep_notes: Union[List[str], Set[str]] = field()
    """The note (by category) to keep in each clinical note.  The rest are
    filtered.

    """
    keep_summary_sections: Union[List[str], Set[str]] = field()
    """The sections to keep in each clinical note.  The rest are filtered."""

    def __post_init__(self):
        super().__post_init__()
        if self.keep_notes is not None and not isinstance(self.keep_notes, set):
            self.keep_notes = frozenset(self.keep_notes)
        if self.keep_summary_sections is not None and \
           not isinstance(self.keep_summary_sections, set):
            self.keep_summary_sections = frozenset(self.keep_summary_sections)

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

    def load(self, name: str) -> AdmissionAmrFeatureDocument:
        """Load an admission from the MIMIC-III package and parse it for
        language and AMRs.

        :param name: the MIMIC-III admission ID

        :return: the parsed admission

        """
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'loading admission: {name}...')
        # MIMIC components index admissions and notes by ints
        hadm_id = int(name)
        if not self.exists(hadm_id):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'no admission: {hadm_id}')
            return None
        notes: List[_NoteIndex] = []
        sents: List[AmrFeatureSentence] = []
        fails: List[ParseFailure] = []
        adm: HospitalAdmission = self.corpus.get_hospital_adm_by_id(hadm_id)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'admin retrieved: {adm}')
        ds_cat: str = DischargeSummaryNote.CATEGORY
        by_cat: Dict[str, List[int]] = self.corpus.note_event_persister.\
            get_row_ids_by_category(int(hadm_id), self.keep_notes)
        ds_notes: List[int] = by_cat[ds_cat]
        if len(ds_notes) == 0:
            raise MimicError(
                f'No discharge sumamries for admission: {adm.hadm_id}')
        # take only the most recent (sorted in DB layer)
        ds_note: Note = adm[ds_notes[0]]
        ds_ix: _NoteIndex = self._load_note(
            ds_note, self.keep_summary_sections, sents, fails)
        cat: str
        row_ids: List[int]
        for cat, row_ids in by_cat.items():
            if cat != ds_cat:
                notes.extend(map(
                    lambda i: self._load_note(adm[str(i)], None, sents, fails),
                    sorted(row_ids)))
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'parsed {len(sents)} sentences not including ' +
                        f'{len(fails)} AMR parse failures')
        doc = AdmissionAmrFeatureDocument(
            sents=tuple(sents),
            amr=AmrDocument(tuple(map(lambda s: s.amr, sents))),
            hadm_id=adm.hadm_id,
            _ds_ix=ds_ix,
            _ant_ixs=tuple(notes),
            parse_fails=fails)
        doc.amr.reindex_variables()
        if self.amr_annotator.coref_resolver is not None:
            logger.info('resolving coreferences...')
            self.amr_annotator.coref_resolver(doc)
        return doc

    def keys(self) -> Iterable[str]:
        # bypass cache stash
        return map(str, self.corpus.admission_persister.get_keys())

    def exists(self, name: str) -> bool:
        # bypass cache stash
        return self.corpus.admission_persister.exists(int(name))
