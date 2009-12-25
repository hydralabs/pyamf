# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 The PyAMF Project.
# See LICENSE.txt for details.
#
# PyAMF documentation build configuration file.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this file.
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.

import sys, os, time

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute.
sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../pyamf'))
sys.path.append(os.path.abspath('html'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']

# Paths that contain templates, relative to this directory.
templates_path = ['html']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
#master_doc = 'index'

# create content template for the homepage
from util import rst2html, copy_file
readme = rst2html('../README.txt', 'html/intro.html')
readme = copy_file('../CHANGES.txt', 'changelog.rst')

# Location of the PyAMF source root folder.
sys.path.insert(0, os.path.abspath('../pyamf'))
import pyamf

# General substitutions.
project = 'PyAMF'
url = 'http://pyamf.org'
description = 'AMF for Python'
copyright = "Copyright &#169; 2007-%s The <a href='%s'>%s</a> Project. All rights reserved." % (
            time.strftime('%Y'), url, project)

# We look for the __init__.py file in the current PyAMF source tree
# and replace the values accordingly.
#
# The short X.Y version.
release = '.'.join(map(lambda x: str(x), pyamf.__version__))
# The full version, including alpha/beta/rc tags.
version = release[:3]

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# A list of directory paths, relative to the source directory, that are to
# be recursively excluded from the search for source files, that is, their
# subdirectories won’t be searched too.
exclude_trees = ['_build', 'tutorials/examples']

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'trac'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = 'default.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = '%s - %s' % (project, description)

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['html/static']

# The name of an image file (.ico) that is the favicon of the docs.
html_favicon = 'pyamf.ico'

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    'toc': 'sidebartoc.html'
}

# Additional templates that should be rendered to pages, maps page names to
# template names.
html_additional_pages = {
    'download': 'download.html',
    'index': 'indexcontent.html',
}

# Content template for the index page, filename relative to this file.
html_index = 'indexcontent.html'

# If false, no module index is generated.
html_use_modindex = True

# If true, the reST sources are included in the HTML build as _sources/<name>.
html_copy_source = True

# Output an OpenSearch description file.
html_use_opensearch = 'http://docs.pyamf.org'

# Output file base name for HTML help builder.
htmlhelp_basename = 'pyamf' + release.replace('.', '')

# Split the index
html_split_index = True


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'PyAMF.tex', html_title,
   copyright, 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/': None}