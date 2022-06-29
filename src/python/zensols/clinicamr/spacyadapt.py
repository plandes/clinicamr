"""A set of adaptor classes from :class:`zensols.nlp.FeatureToken` to
:class:`spacy.tokens.Doc`.

"""
__author__ = 'Paul Landes'

from typing import Dict
from zensols.config import persisted
from zensols.nlp import TokenContainer, FeatureToken


class Underscore(object):
    pass


class SpacyTokenAdapter(object):
    def __init__(self,  ftok: FeatureToken, sent):
        self._ftok = ftok
        self.sent = sent

    def __getattr__(self, attr, default=None):
        v = None
        if attr == 'text':
            v = self._ftok.norm
        elif attr == 'ent_type_':
            v = self._ftok.ent_
            if v == FeatureToken.NONE:
                v = ''
        elif attr == 'doc':
            v = self.sent._doc
        else:
            v = getattr(self._ftok, attr)
        return v

    def __str__(self):
        return self._ftok.norm


class SpacySpanAdapter(object):
    def __init__(self, cont: TokenContainer, doc):
        self._cont = cont
        self._doc = doc
        self._ = Underscore()
        self._toks = tuple(map(lambda t: SpacyTokenAdapter(t, self),
                               self._cont.token_iter()))

    @property
    def text(self):
        return self._cont.norm

    @property
    def start(self):
        return self._cont[0].i

    def __getitem__(self, i):
        ta: SpacyTokenAdapter = self._i_to_tok()[i]
        return ta

    def __iter__(self):
        return iter(self._toks)


class SpacyDocAdapter(SpacySpanAdapter):
    def __init__(self, cont: TokenContainer):
        super().__init__(cont, cont)

    @persisted('_i_to_tok_pw')
    def _i_to_tok(self) -> Dict[int, SpacyTokenAdapter]:
        return {ta._ftok.i: ta for ta in self}

    @property
    @persisted('_sents')
    def sents(self):
        return tuple(map(lambda s: SpacySpanAdapter(s, self), self._cont.sents))
