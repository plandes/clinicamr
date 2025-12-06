"""Prototyping module.

"""
from zensols.config import ConfigFactory
from pathlib import Path
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

    def _test_parse(self, dump: bool = False):
        parser = self.config_factory('amr_anon_doc_parser')
        parser.clear()
        doc = parser(Path('test-resources/clinical-example.txt').read_text())
        doc.write()
        if dump:
            import os
            from zensols.amr import Dumper
            dumper: Dumper = self.config_factory('amr_dumper')
            path: Path = dumper(doc.amr)
            os.system(path)

    def _test_load(self):
        from zensols.util.time import time
        from zensols.clinicamr.adm import AdmissionAmrFactoryStash
        self._clear()
        stash: AdmissionAmrFactoryStash = self.config_factory('camr_adm_amr_stash')
        #hadm_id: str = '134891'  # human annotated
        hadm_id: str = '151608'  # model annotated
        with time('loaded'):
            adm = stash.load(hadm_id)
        #adm.write()
        for s in adm.sents:
            s.amr.write()

    def proto(self, run: int = 0):
        """Used for rapid prototyping."""
        if 0:
            with open('/d/a.yml', 'w') as f:
                self.config_factory.config.asyaml(writer=f)
            return
        {0: self._test_parse,
         1: self._test_load,
         }[run]()
