"""The basic dict based notebook format.

The Python representation of a notebook is a nested structure of
dictionary subclasses that support attribute access
(.ipstruct.Struct). The functions in this module are merely
helpers to build the structs in the right form.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import pprint
import uuid

from .ipstruct import Struct

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

# Change this when incrementing the nbformat version
nbformat = 3
nbformat_minor = 0

class NotebookNode(Struct):
    pass


def from_dict(d):
    if isinstance(d, dict):
        newd = NotebookNode()
        for k,v in list(d.items()):
            newd[k] = from_dict(v)
        return newd
    elif isinstance(d, (tuple, list)):
        return [from_dict(i) for i in d]
    else:
        return d


def new_output(output_type=None, output_text=None, output_png=None,
    output_html=None, output_svg=None, output_latex=None, output_json=None,
    output_javascript=None, output_jpeg=None, prompt_number=None,
    ename=None, evalue=None, traceback=None, stream=None, metadata=None):
    """Create a new code cell with input and output"""
    output = NotebookNode()
    if output_type is not None:
        output.output_type = str(output_type)

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise TypeError("metadata must be dict")
    output.metadata = metadata

    if output_type != 'pyerr':
        if output_text is not None:
            output.text = str(output_text)
        if output_png is not None:
            output.png = bytes(output_png)
        if output_jpeg is not None:
            output.jpeg = bytes(output_jpeg)
        if output_html is not None:
            output.html = str(output_html)
        if output_svg is not None:
            output.svg = str(output_svg)
        if output_latex is not None:
            output.latex = str(output_latex)
        if output_json is not None:
            output.json = str(output_json)
        if output_javascript is not None:
            output.javascript = str(output_javascript)

    if output_type == 'pyout':
        if prompt_number is not None:
            output.prompt_number = int(prompt_number)

    if output_type == 'pyerr':
        if ename is not None:
            output.ename = str(ename)
        if evalue is not None:
            output.evalue = str(evalue)
        if traceback is not None:
            output.traceback = [str(frame) for frame in list(traceback)]

    if output_type == 'stream':
        output.stream = 'stdout' if stream is None else str(stream)
    
    return output


def new_code_cell(input=None, prompt_number=None, outputs=None,
    language='python', collapsed=False, metadata=None):
    """Create a new code cell with input and output"""
    cell = NotebookNode()
    cell.cell_type = 'code'
    if language is not None:
        cell.language = str(language)
    if input is not None:
        cell.input = str(input)
    if prompt_number is not None:
        cell.prompt_number = int(prompt_number)
    if outputs is None:
        cell.outputs = []
    else:
        cell.outputs = outputs
    if collapsed is not None:
        cell.collapsed = bool(collapsed)
    cell.metadata = NotebookNode(metadata or {})

    return cell

def new_text_cell(cell_type, source=None, rendered=None, metadata=None):
    """Create a new text cell."""
    cell = NotebookNode()
    # VERSIONHACK: plaintext -> raw
    # handle never-released plaintext name for raw cells
    if cell_type == 'plaintext':
        cell_type = 'raw'
    if source is not None:
        cell.source = str(source)
    if rendered is not None:
        cell.rendered = str(rendered)
    cell.metadata = NotebookNode(metadata or {})
    cell.cell_type = cell_type
    return cell


def new_heading_cell(source=None, rendered=None, level=1, metadata=None):
    """Create a new section cell with a given integer level."""
    cell = NotebookNode()
    cell.cell_type = 'heading'
    if source is not None:
        cell.source = str(source)
    if rendered is not None:
        cell.rendered = str(rendered)
    cell.level = int(level)
    cell.metadata = NotebookNode(metadata or {})
    return cell


def new_worksheet(name=None, cells=None, metadata=None):
    """Create a worksheet by name with with a list of cells."""
    ws = NotebookNode()
    if name is not None:
        ws.name = str(name)
    if cells is None:
        ws.cells = []
    else:
        ws.cells = list(cells)
    ws.metadata = NotebookNode(metadata or {})
    return ws


def new_notebook(name=None, metadata=None, worksheets=None):
    """Create a notebook by name, id and a list of worksheets."""
    nb = NotebookNode()
    nb.nbformat = nbformat
    nb.nbformat_minor = nbformat_minor
    if worksheets is None:
        nb.worksheets = []
    else:
        nb.worksheets = list(worksheets)
    if metadata is None:
        nb.metadata = new_metadata()
    else:
        nb.metadata = NotebookNode(metadata)
    if name is not None:
        nb.metadata.name = str(name)
    return nb


def new_metadata(name=None, authors=None, license=None, created=None,
    modified=None, gistid=None):
    """Create a new metadata node."""
    metadata = NotebookNode()
    if name is not None:
        metadata.name = str(name)
    if authors is not None:
        metadata.authors = list(authors)
    if created is not None:
        metadata.created = str(created)
    if modified is not None:
        metadata.modified = str(modified)
    if license is not None:
        metadata.license = str(license)
    if gistid is not None:
        metadata.gistid = str(gistid)
    return metadata

def new_author(name=None, email=None, affiliation=None, url=None):
    """Create a new author."""
    author = NotebookNode()
    if name is not None:
        author.name = str(name)
    if email is not None:
        author.email = str(email)
    if affiliation is not None:
        author.affiliation = str(affiliation)
    if url is not None:
        author.url = str(url)
    return author

