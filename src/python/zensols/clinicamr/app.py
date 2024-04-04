"""Clincial Domain Abstract Meaning Representation Graphs

"""
__author__ = 'Paul Landes'

from typing import List, Tuple
from dataclasses import dataclass, field
import logging
from pathlib import Path
import pandas as pd
from zensols.config import ConfigFactory
from zensols.persist import Stash
from zensols.cli import ApplicationError
from zensols.nlp import FeatureToken, FeatureDocumentParser

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Clincial Domain Abstract Meaning Representation Graphs.

    """
    config_factory: ConfigFactory = field()
    """For prototyping."""

    doc_parser: FeatureDocumentParser = field()
    """The document parser used for the :meth:`parse` action."""

    dumper: 'Dumper' = field()
    """Plots and writes AMR content in human readable formats."""

    def __post_init__(self):
        FeatureToken.WRITABLE_FEATURE_IDS = tuple('norm cui_'.split())

    def _generate_adm(self, hadm_id: str) -> pd.DataFrame:
        from typing import List, Dict, Any
        from zensols.mimic import Section, Note, HospitalAdmission
        from zensols.mimic.regexnote import DischargeSummaryNote
        from zensols.amr import (
            AmrFeatureSentence, AmrFeatureDocument,
            AmrGeneratedSentence, AmrGeneratedDocument,
        )
        from zensols.amr.model import AmrGenerator

        if logger.isEnabledFor(logging.INFO):
            logger.info(f'generating admission {hadm_id}')
        generator: AmrGenerator = self.config_factory('amr_generator_amrlib')
        stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        if len(ds_notes) == 0:
            raise ApplicationError(
                f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'generating from note {ds_note}')
        rows: List[Tuple[Any, ...]] = []
        cols: List[str] = 'hadm_id note_id sec_id sec_name org gen'.split()
        sec: Section
        for sec in ds_note.sections.values():
            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    f'generating sentences for section {sec.name} ({sec.id})')
            para: AmrFeatureDocument
            for para in sec.paragraphs:
                gen_para: AmrGeneratedDocument = generator(para.amr)
                assert len(gen_para) == len(para)
                sent: AmrFeatureSentence
                gen_sent: AmrGeneratedSentence
                for sent, gen_sent in zip(para, gen_para):
                    rows.append((hadm_id, ds_note.row_id, sec.id, sec.name,
                                 sent.norm, gen_sent.text))
        return pd.DataFrame(rows, columns=cols)

    def generate(self, ids: str, output_dir: Path = None):
        """Creates samples of generated AMR text by first parsing clinical
        sentences into graphs.

        :param ids: a comma separated list of admission IDs to generate

        :param output_dir: the output directory

        """
        if output_dir is None:
            output_dir = self.dumper.target_dir
        output_path = output_dir / 'generated-sents.csv'
        hadm_ids: List[str] = ids.split(',')
        dfs: Tuple[pd.DataFrame] = tuple(map(self._generate_adm, hadm_ids))
        df: pd.DataFrame = pd.concat(dfs)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path)
        logger.info(f'wrote: {output_path}')


@dataclass
class PrototypeApplication(object):
    CLI_META = {'is_usage_visible': False}

    config_factory: ConfigFactory = field()
    app: Application = field()

    def _clear(self):
        self.config_factory('clear_cli').clear()

    def _test_parse(self, clear_data: bool = True,
                    print_toks: bool = True,
                    dump: bool = True):
        from zensols.amr import AmrFeatureDocument

        self._clear()
        sent = """58 y/o M with multiple myeloma s/p chemo and auto SCT [**4-27**]
presenting with acute onset of CP and liver failure"""
        sent = """Mr. [**Known lastname **] from the United States is an 87 yo male with a
history of diastolic CHF (EF\n65% 1/10)."""
        sent = 'He was diagnosed with kidney failure'
        parser = self.app.doc_parser
        #self.config_factory.config['amr_anon_doc_parser'].write()
        #parser = self.config_factory('camr_medical_doc_parser')
        #parser = self.config_factory('amr_anon_doc_parser')
        #parser = self.config_factory('mednlp_combine_doc_parser')
        #parser = self.config_factory('mednlp_doc_parser')
        #parser = self.config_factory('camr_medical_doc_parser')
        doc: AmrFeatureDocument = parser(sent)
        if print_toks:
            for i, t in enumerate(doc.tokens):
                print(f'<{i}/{t.i}/{t.i_sent}>: <{t.norm}/{t.text}>, <{t.ent_} ({t.cui_})>')
            print('_' * 40)
        doc.amr.write()
        if dump:
            dumper = self.config_factory('amr_dumper')
            dumper.render(doc.amr)

    def _test_paragraphs(self):
        from typing import Dict
        from zensols.mimic import Note, HospitalAdmission
        from zensols.mimic.regexnote import DischargeSummaryNote
        from zensols.amr import AmrFeatureDocument

        self._clear()
        nlg = self.config_factory('amr_generator_amrlib')
        if 0:
            print(type(nlg))
            nlg.installer.write()
            return
        dumper = self.config_factory('amr_dumper')
        hadm_id: str = '134891'
        hadm_id: str = '124656'
        stash: Stash = self.config_factory('mimic_corpus').hospital_adm_stash
        adm: HospitalAdmission = stash[hadm_id]
        by_cat: Dict[str, Tuple[Note]] = adm.notes_by_category
        ds_notes: Tuple[Note] = by_cat[DischargeSummaryNote.CATEGORY]
        if len(ds_notes) == 0:
            raise ApplicationError(
                f'No discharge sumamries for admission: {hadm_id}')
        ds_notes = sorted(ds_notes, key=lambda n: n.chartdate, reverse=True)
        ds_note: Note = ds_notes[0]
        #sec: Section = ds_note.sections_by_name['history-of-present-illness'][0]
        import itertools as it
        for sec in it.islice(ds_note.sections.values(), 1):
            if 0:
                print(sec.text)
                print('_' * 80)
            paras = tuple(sec.paragraphs)
            if 1:
                para: AmrFeatureDocument
                for para in it.islice(paras, 1):
                    print(para.text)
                    print()
                    if 1:
                        print(para.amr.graph_string)
                        print('_' * 80)
            if 0:
                for t in paras[0][1]:
                    print(t, t.cui_, t.ent_, t.is_concept)
            if 0:
                dumper.clean()
                dumper.overwrite_dir = False
                for pix, para in enumerate(paras):
                    dumper(para.amr, f'p-{pix}')

    def _tmp(self):
        from zensols.amr import AmrFeatureDocument
        sent = """58 y/o M with multiple myeloma s/p chemo and auto SCT [**4-27**]
presenting with acute onset of CP and liver failure"""
        sent = """sulfites/[**DoctorLastName**] Juice, Lime Juice, Sauerkraut"""
        #sent = """sulfites/[**Doctor Last Name**] Juice, Lime Juice, Sauerkraut"""
        sent = """sulfites/[**DoctorLastName5942**] Juice, Lime Juice, Sauerkraut"""
        #sent = """sulfites/[**SomeStuff**] Juice, Lime Juice, Sauerkraut"""
        #dp = self.config_factory('amr_base_doc_parser')
        #dp = self.config_factory('mednlp_combine_biomed_doc_parser')
        #dp = self.config_factory('doc_parser')
        dp = self.app.doc_parser
        doc: AmrFeatureDocument = dp(sent)
        for t in doc.tokens:
            print(t.norm, t.text, t.ent_, t.mimic_, t.onto_)
        doc.write(include_relation_set=True)
        print(doc.amr.graph_string)

    def _tmp(self):
        sent = '2. smaller PE in the RML and RUL branches.'
        sent = 'Pt was discharged from the oncology service yesterday, when she noticed the onset of severe pleuritic chest pain.'
        if 0:
            import re
            linker = self.app.config_factory('entity_linker_resource')
            ent = linker.get_linked_entity('C1555459')
            ent.write()
            html_tag = re.compile('<.*?>')
            desc = re.sub(html_tag, '', ent.definition)
            print(desc)
            return
        if 0:
            for i in 'app clinicamr_default camr_doc_parser amr_anon_doc_parser mednlp_combine_biomed_doc_parser'.split():
                self.app.config_factory.config[i].write()
                print()
            return
        if 0:
            print(type(self.app.doc_parser))
            print(type(self.app.doc_parser.delegate))
            return
        dp = self.app.doc_parser
        doc: AmrFeatureDocument = dp(sent)
        doc.write()
        print(doc.amr.graph_string)
        dumper = self.config_factory('amr_dumper')
        dumper(doc.amr)

    def _tmp(self):
        #self.app.generate('110132')
        #self.app.config_factory.config.write()
        sent = """58 y/o M with multiple myeloma s/p chemo and auto SCT [**4-27**]
presenting with acute onset of CP and liver failure"""
        self.app.predict(sent)

    def proto(self, run: int = 4):
        """Used for rapid prototyping."""
        {0: self._tmp,
         3: self._test_parse,
         4: self._test_paragraphs,
         5: self.app.generate,
         }[run]()
