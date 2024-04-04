import unittest
import sys
from pathlib import Path
import shutil
from zensols.config import ImportIniConfig, ImportConfigFactory
from zensols.nlp import FeatureDocument
from zensols.amr import AmrDocument, AmrFeatureDocument


if 0:
    import logging
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger('zensols.amr').setLevel(logging.DEBUG)


class TestParser(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = sys.maxsize
        super().__init__(*args, **kwargs)
        conf = ImportIniConfig('test-resources/test.conf')
        fac = ImportConfigFactory(conf)
        self.doc_parser = fac('amr_anon_doc_parser')
        #self.doc_parser = fac('camr_medical_doc_parser')
        targ_dir = Path('target')
        if targ_dir.is_dir():
            shutil.rmtree(targ_dir)

    def test_parse(self):
        DO_WRITE = 0
        DEBUG = 0
        text = """Mr. [**Known lastname **] from the United States is an 87 yo male with a
history of diastolic CHF (EF\n65% 1/10) and kidney failure."""
        doc: FeatureDocument = self.doc_parser(text)
        if DEBUG:
            print(doc.norm)
            for i, t in enumerate(doc.token_iter()):
                print(f'<{i}/{t.i}/{t.i_sent}>: <{t.norm}/{t.text}>, <{t.ent_} ({t.cui_})>')
            doc.write()
        self.assertEqual(AmrFeatureDocument, type(doc))
        self.assertEqual(1, len(doc))
        should = ('Mr.', 'KNOWNLASTNAME', 'from', 'the', 'United', 'States',
                  'is', 'an', '87', 'yo', 'male',
                  'with', 'a', 'history', 'of', 'diastolic', 'CHF',
                  '(', 'EF', '65', '%', '1/10', ')',
                  'and', 'kidney', 'failure', '.')
        self.assertEqual(should, tuple(doc.norm_token_iter()))
        amr_doc: AmrDocument = doc.amr
        self.assertTrue(isinstance(amr_doc, AmrDocument))
        should_file = 'test-resources/amr-graph.txt'
        if DO_WRITE:
            with open(should_file, 'w') as f:
                f.write(amr_doc.graph_string)
        with open(should_file) as f:
            should = f.read().strip()
        self.assertEqual(should, amr_doc.graph_string)
