from __future__ import print_function

from lena.output import hist1d_to_csv, hist2d_to_csv, ToCSV
from lena.structures import Histogram


def test_hist_to_csv():
    hist = Histogram(edges=[0, 1, 2], bins=[1, 2])
    # test defaults
    assert list(hist1d_to_csv(hist)) == [
            '0.000000,1.000000', '1.000000,2.000000', '2.000000,2.000000']
    # header, duplicate_last_bin
    assert list(hist1d_to_csv(hist, duplicate_last_bin=False, header='x,bin')) == [
            'x,bin', '0.000000,1.000000', '1.000000,2.000000']
    # separator
    assert list(hist1d_to_csv(hist, separator=' ', header='x bin')) == [
            'x bin', '0.000000 1.000000', '1.000000 2.000000', '2.000000 2.000000']

    hist_to_csv = ToCSV()
    hist_data = list(hist.compute())
    assert list(hist_to_csv.run(hist_data)) == [(
                '0.000000,1.000000\n1.000000,2.000000\n2.000000,2.000000',
                {'output': {'filetype': 'csv'},
                    'histogram': {'ranges': [(0, 2)], 'dim': 1, 'nbins': [2]}}
            )]

    hist = Histogram(edges=[[0, 1, 2], [0, 2, 4]], bins=[[1, 2], [3, 4]])
    hist_data = list(hist.compute())
    assert list(hist2d_to_csv(hist)) == [
            '0.000000,0.000000,1.000000', '0.000000,2.000000,2.000000', '0.000000,4.000000,2.000000', '1.000000,0.000000,3.000000', '1.000000,2.000000,4.000000', '1.000000,4.000000,4.000000', '2.000000,0.000000,3.000000', '2.000000,2.000000,4.000000', '2.000000,4.000000,4.000000']
    assert list(hist2d_to_csv(hist, header='x,y,z')) == [
            'x,y,z', '0.000000,0.000000,1.000000', '0.000000,2.000000,2.000000', '0.000000,4.000000,2.000000', '1.000000,0.000000,3.000000', '1.000000,2.000000,4.000000', '1.000000,4.000000,4.000000', '2.000000,0.000000,3.000000', '2.000000,2.000000,4.000000', '2.000000,4.000000,4.000000']
    assert list(hist2d_to_csv(hist, duplicate_last_bin=False)) == [
            '0.000000,0.000000,1.000000', '0.000000,2.000000,2.000000', '1.000000,0.000000,3.000000', '1.000000,2.000000,4.000000']
    assert list(hist2d_to_csv(hist, separator=' ')) == [
            '0.000000 0.000000 1.000000', '0.000000 2.000000 2.000000', '0.000000 4.000000 2.000000', '1.000000 0.000000 3.000000', '1.000000 2.000000 4.000000', '1.000000 4.000000 4.000000', '2.000000 0.000000 3.000000', '2.000000 2.000000 4.000000', '2.000000 4.000000 4.000000']

    hist_to_csv = ToCSV(duplicate_last_bin=False)
    assert list(hist_to_csv.run(hist_data)) == [(
        '0.000000,0.000000,1.000000\n0.000000,2.000000,2.000000\n1.000000,0.000000,3.000000\n1.000000,2.000000,4.000000', {'output': {'filetype': 'csv'}, 'histogram': {'ranges': [(0, 2), (0, 4)], 'dim': 2, 'nbins': [2, 2]}}
        )]
