"""Fixes for the Python domain."""

import json
import re
from typing import (
    cast,
    Sequence,
    Tuple,
    List,
    Dict,
    Type,
    Optional,
    Any,
    Iterator,
    Union,
)

import docutils.nodes
import docutils.parsers.rst.states
import sphinx
import sphinx.addnodes
import sphinx.application
import sphinx.builders
import sphinx.domains
import sphinx.domains.python
import sphinx.environment
import sphinx.errors
import sphinx.ext.napoleon
import sphinx.util.logging
import sphinx.util.nodes

from ... import sphinx_utils
from . import autodoc_property_type

PythonDomain = sphinx.domains.python.PythonDomain
PyTypedField = sphinx.domains.python.PyTypedField
PyObject = sphinx.domains.python.PyObject


logger = sphinx.util.logging.getLogger(__name__)


def setup(app: sphinx.application.Sphinx):
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
