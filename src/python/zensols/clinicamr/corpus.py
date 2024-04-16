"""Classes used to parse the clinical corpus into an annotated AMR corpus.

"""
__author__ = 'Paul Landes'

from typing import Tuple, Dict, Iterable
from dataclasses import dataclass, field
from zensols.persist import Stash, ReadOnlyStash
from zensols.mimic import MimicError, Section, Note, HospitalAdmission
from zensols.mimic import Corpus as MimicCorpus
from zensols.mimic.regexnote import DischargeSummaryNote
from zensols.amr import (
    AmrFeatureSentence, AmrFeatureDocument, AmrSentence, AmrDocument
)


@dataclass
class CorpusFactoryStash(ReadOnlyStash):
    mimic_corpus: MimicCorpus = field()

    def load(self, hadm_id: str) -> AmrFeatureDocument:
        pdocs = []
        stash: Stash = self.mimic_corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        if len(ds_notes) == 0:
            raise MimicError(
                f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        sec: Section = ds_note.sections_by_name['history-of-present-illness'][0]
        for sec in [sec]:
            paras = tuple(sec.paragraphs)
            para: AmrFeatureDocument
            for para in paras:
                assert isinstance(para, AmrFeatureDocument)
                assert isinstance(para.amr, AmrDocument)
                print(para.text)
                print('-')
                for s in para:
                    assert isinstance(s, AmrFeatureSentence)
                    assert isinstance(s.amr, AmrSentence)
                    print(s.norm)
                    print()
                print('_' * 80)
                pdocs.append(para)
        return para

    def keys(self) -> Iterable[str]:
        return self.corpus.hospital_adm_stash.keys()

    def exists(self, hadm_id: str) -> bool:
        return self.corpus.hospital_adm_stash.exists(hadm_id)
