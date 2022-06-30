import unittest
import sys
from zensols.config import ImportIniConfig, ImportConfigFactory
from zensols.nlp import FeatureDocument
from zensols.amr import AmrDocument, AmrFeatureDocument


class TestParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = sys.maxsize
        super().__init__(*args, **kwargs)
        conf = ImportIniConfig('test-resources/test.conf')
        fac = ImportConfigFactory(conf)
        self.doc_parser = fac('mednlp_combine_doc_parser')
        self.ann = fac('amr_annotator')

    def test_parse(self):
        text = """Mr. [**Known lastname **] is an 87 yo male with a
history of diastolic CHF (EF\n65% 1/10)."""
        doc: FeatureDocument = self.doc_parser(text)
        if 0:
            print(doc.tokens)
        should = ('Mr', '.', 'LASTNAME', 'is', 'an', '87', 'yo', 'male',
                  'with', 'a', 'history of', 'diastolic', 'CHF',
                  '(', 'EF', '65', '%', '1/10', ')', '.')
        self.assertEqual(should, tuple(doc.norm_token_iter()))
        amr_feat_doc: AmrFeatureDocument = self.ann(doc)
        self.assertTrue(isinstance(amr_feat_doc, AmrFeatureDocument))
        amr_doc: AmrDocument = amr_feat_doc.amr
        self.assertTrue(isinstance(amr_doc, AmrDocument))
        with open('test-resources/amr-graph.txt') as f:
            should = f.read().strip()
        self.assertEqual(should, amr_doc.graph_string)
