"""Sphinx configuration for Tatiana Kaado's EECE 435L Lab 4 project."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

project = 'School Management System — Tkinter and PyQt5'
author = 'Tatiana Kaado'
copyright = '2026, Tatiana Kaado'
version = '1.0'
release = '1.0.0'
language = 'en'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
]
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f'{project} {release} documentation'
html_show_copyright = True
html_theme_options = {'navigation_depth': 3}
autodoc_member_order = 'bysource'
autodoc_typehints = 'signature'
autodoc_default_options = {
    'ignore-module-all': True,
    'private-members': True,
    'special-members': '__init__,__post_init__',
    'exclude-members': '_abc_impl',
}
viewcode_follow_imported_members = False
# Constructors are documented once as explicit members, with class overviews above.
add_module_names = False
