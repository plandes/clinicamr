from zensols.nlp import FeatureDocument
from zensols.amr import AmrDocument, AmrFeatureDocument
from util import TestBase


class TestParser(TestBase):
    def test_parse(self):
        WRITE = 0
        DEBUG = 0
        text = """Mr. [**Known lastname **] from the United States is an 87 yo male with a
history of diastolic CHF (EF\n65% 1/10) and kidney failure."""
        doc: FeatureDocument = self.doc_parser(text)
        if DEBUG:
            print(doc.norm)
            for i, t in enumerate(doc.token_iter()):
                print(f'<{i}/{t.i}/{t.i_sent}>: <{t.norm}/{t.text}>, <{t.ent_} ({t.cui_})>')
            doc.amr.write()
        self.assertEqual(AmrFeatureDocument, type(doc))
        self.assertEqual(1, len(doc))
        self.assertEqual(27, len(doc[0]))
        self.assertEqual(tuple(range(len(doc[0]))),
                         tuple(map(lambda t: t.i_sent, doc.token_iter())))
        should = ('Mr.', 'KNOWNLASTNAME', 'from', 'the', 'United', 'States',
                  'is', 'an', '87', 'yo', 'male',
                  'with', 'a', 'history', 'of', 'diastolic', 'CHF',
                  '(', 'EF', '65', '%', '1/10', ')',
                  'and', 'kidney', 'failure', '.')
        self.assertEqual(should, tuple(doc.norm_token_iter()))
        amr_doc: AmrDocument = doc.amr
        self.assertTrue(isinstance(amr_doc, AmrDocument))
        should_file = 'test-resources/amr-graph.txt'
        if WRITE:
            with open(should_file, 'w') as f:
                f.write(amr_doc.graph_string)
        with open(should_file) as f:
            should = f.read().strip()
        self.assertEqual(should, amr_doc.graph_string)
