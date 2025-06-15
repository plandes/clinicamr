"""Command line entry point to the application.

"""
__author__ = 'Paul Landes'

from typing import List, Any, Type, Dict
import sys
from zensols.cli import ActionResult, CliHarness
from zensols.cli import ApplicationFactory as CliApplicationFactory


class ApplicationFactory(CliApplicationFactory):
    def __init__(self, *args, **kwargs):
        kwargs['package_resource'] = 'zensols.clinicamr'
        super().__init__(*args, **kwargs)

    @classmethod
    def get_corpus(cls: Type) -> 'Corpus':
        harness: CliHarness = cls.create_harness()
        return harness['mimic_corpus']

    @classmethod
    def get_doc_parser(cls: Type) -> 'FeatureDocumentParser':
        harness: CliHarness = cls.create_harness()
        config_factory = harness.get_config_factory()
        return config_factory('clinicamr_default').doc_parser

    @classmethod
    def get_admission_amr_stash(cls: Type) -> 'AdmissionAmrFeatureDocument':
        harness: CliHarness = cls.create_harness()
        config_factory = harness.get_config_factory()
        return config_factory('camr_adm_amr_stash')


def main(args: List[str] = sys.argv, **kwargs: Dict[str, Any]) -> ActionResult:
    harness: CliHarness = ApplicationFactory.create_harness(relocate=False)
    harness.invoke(args, **kwargs)
