from __future__ import print_function

import os
import pytest
import subprocess
import sys

import lena.core
from lena.output import PDFToPNG


def test_pdf_to_png(mocker):
    mocker.patch('subprocess.Popen.communicate', return_value=("stdout", "stderr"))
    mocker.patch('subprocess.Popen.returncode', return_value=True, create=True)
    mocker.patch('subprocess.Popen', return_value=subprocess.Popen)

    pdf_to_png = PDFToPNG()
    data = [
        ("output/file.csv", {"output": {"filename": "y", "filetype": "csv"}}),
        ("output/file.pdf", {"output": {"filename": "y", "filetype": "pdf"}}),
    ]
    res = list(pdf_to_png.run(data))
    assert res ==  [
        ('output/file.csv', {'output': {'filename': 'y', 'filetype': 'csv'}}),
        # since no png file exists,
        # mocker imitates creation of a new one, thus changed=True
        ('output/file.png', {'output': {'changed': True,
                                        'filename': 'y', 'filetype': 'png'}})
    ]

    command = ['pdftoppm', 'output/file.pdf', 'output/file', '-png', '-singlefile']
    subprocess.Popen.assert_called_once_with(command)
