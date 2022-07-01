"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
from pathlib import Path
import pandas as pd
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.nlp import FeatureToken, FeatureDocumentParser
from zensols.mimic import Corpus, Note, HospitalAdmission
from zensols.mimicsid import AnnotationResource

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    CLI_META = {'option_includes': set('text hadm_id'.split())}

    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    corpus: Corpus = field()
    """A container class for the resources that access the MIMIC-III corpus."""

    anon_resource: AnnotationResource = field()
    """Contains resources to access the MIMIC-III MedSecId annotations."""

    plot_path: Path = field()
    """Base path to add AMR graphs."""

    amr_paragraph_stash: Stash = field()
    """The stash that caches paragraph AMR graphs."""

    def __post_init__(self):
        FeatureToken.WRITABLE_FEATURE_IDS = tuple('norm cui_'.split())

    def parse(self, text: str = None):
        """Parse a MIMIC-III string.

        :param text: the text to parse

        """
        text = 'He died of liver failure.' if text is None else text
        doc = self.doc_parser(text)
        doc.sents[0].write()
        sent = doc.sents[0]
        if hasattr(sent, 'amr'):
            print(doc.amr)
            doc.amr.plot(Path('/d/amr'))

    def clear(self):
        """Clear the paragraph AMR cache."""
        logger.info(f'removing files in: {self.amr_paragraph_stash.path}')
        self.amr_paragraph_stash.clear()

    def _tmp1(self):
        """Used for rapid prototyping."""
        hadm_id = '119960'
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        note = adm.notes_by_category['Discharge summary'][0]
        sec = note.sections['history-of-present-illness']
        for para in sec.paragraphs:
            para.amr.plot(self.plot_path / f'{adm.hadm_id}-{note.row_id}')

    def plot(self, hadm_id: str = '119960'):
        """Create plots for an admission."""
        parser_model: str = self.config_factory.config.get_option(
            'parse_model', section='amr_default')
        df: pd.DataFrame = self.anon_resource.note_ids
        stash: Stash = self.corpus.hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        anon_row_ids = df[df['hadm_id'] == hadm_id]['row_id'].astype(int).tolist()
        note: Note
        for note in map(lambda i: adm.notes_by_id[i], anon_row_ids):
            id_dir: str = f'{adm.hadm_id}-{note.row_id}'
            note_path: Path = self.plot_path / parser_model / id_dir
            print(note)
            for sec in note.sections.values():
                try:
                    for para in sec.paragraphs:
                        para.amr.plot(note_path)
                except Exception as e:
                    print(f'Error: {e}')

    def proto(self):
        """Used for rapid prototyping."""
        self.plot()
