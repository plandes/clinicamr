"""Prototyping module.

"""
from zensols.nlp import FeatureToken
from zensols.config import ConfigFactory
from dataclasses import dataclass, field
from .app import Application


@dataclass
class PrototypeApplication(object):
    CLI_META = {'is_usage_visible': False}

    config_factory: ConfigFactory = field()
    app: Application = field()

    def _clear(self, only_para: bool = False):
        if only_para:
            self.config_factory('camr_paragraph_factory').clear()
            self.config_factory('camr_adm_amr_stash').clear()
        else:
            self.config_factory('clear_cli').clear()

    def _test_parse(self):
        parser = self.config_factory('amr_anon_doc_parser')
        doc = parser('John Smith was diagnosed with kidney failure.')
        doc.write()
        t: FeatureToken
        for t in doc.token_iter():
            t.write(feature_ids='norm ent_ cui_'.split(), inline=True)

    def _test_load(self):
        from zensols.util.time import time
        from zensols.clinicamr.adm import AdmissionAmrFactoryStash
        #self._clear(1)
        self._clear()
        stash: AdmissionAmrFactoryStash = self.config_factory('camr_adm_amr_stash')
        #hadm_id: str = '134891'  # human annotated
        hadm_id: str = '151608'  # model annotated
        with time('loaded'):
            adm = stash.load(hadm_id)
        #adm.write()
        for s in adm.sents:
            s.amr.write()

    def proto(self, run: int = 1):
        """Used for rapid prototyping."""
        {0: self._test_parse,
         1: self._test_load,
         }[run]()
