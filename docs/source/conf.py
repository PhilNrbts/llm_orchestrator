import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

project = 'LLM Orchestrator'
copyright = '2025, baggy'
author = 'baggy'
release = '0.1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'myst_parser',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'furo'
html_static_path = ['_static']
