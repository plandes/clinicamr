"""Application comain classes

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
from zensols.util import APIError

logger = logging.getLogger(__name__)


class ClinicalAmrError(APIError):
    pass
