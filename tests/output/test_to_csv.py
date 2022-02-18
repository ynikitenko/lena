from lena.output import hist1d_to_csv, hist2d_to_csv, ToCSV, iterable_to_table
from lena.structures import histogram, Histogram, graph


def test_iterable_to_table():
    # one-dimensional structure is output correctly
    it0 = (1, 2, 3.5, 4)
    #     iterable, format_=None, header="", header_fields=(),
    #     row_start="", row_end="", row_separator=",",
    #     footer=""
    assert r"\n".join(
        iterable_to_table(it0, row_start="b", row_end="e", row_separator="s",
                          footer="f")
    ) == r'b1e\nb2e\nb3.5e\nb4e\nf'

    # for now not needed, 100% coverage by docstrings.
    # it = ((1, 2), (3.5, 4))


def test_to_csv():
    hist = histogram(edges=[0, 1, 2], bins=[1, 2])
    gr = graph([[0, 1], [2.5, 3]])
    to_csv = ToCSV(separator=",", header=None, duplicate_last_bin=True)

    ## histogram and iterables work, other values passed unchanged
    # no context works fine
    res1 = list(to_csv.run([hist, gr, 3]))
    # data parts are correct
    data_1 = [res1[0][0], res1[1][0], res1[2]]
    # assert list(to_csv.run([hist, gr, 3])) == []
    assert data_1 == [
        '0.000000,1.000000\n1.000000,2.000000\n2.000000,2.000000',
        '0,2.5\n1,3',
        3
    ]


def test_hist_to_csv():
    hist = histogram(edges=[0, 1, 2], bins=[1, 2])
    # test defaults
    assert list(hist1d_to_csv(hist)) == [
            '0.000000,1.000000', '1.000000,2.000000', '2.000000,2.000000']
    # header, duplicate_last_bin
    assert list(hist1d_to_csv(hist, duplicate_last_bin=False, header='x,bin')) == [
            'x,bin', '0.000000,1.000000', '1.000000,2.000000']
    # separator
    assert list(hist1d_to_csv(hist, separator=' ', header='x bin')) == [
            'x bin', '0.000000 1.000000', '1.000000 2.000000', '2.000000 2.000000']

    hist = Histogram(edges=[0, 1, 2], bins=[1, 2])
    to_csv = ToCSV()
    hist_data = list(hist.compute())
    assert list(to_csv.run(hist_data)) == [(
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

    to_csv = ToCSV(duplicate_last_bin=False)
    assert list(to_csv.run(hist_data)) == [(
        '0.000000,0.000000,1.000000\n0.000000,2.000000,2.000000\n1.000000,0.000000,3.000000\n1.000000,2.000000,4.000000', {'output': {'filetype': 'csv'}, 'histogram': {'ranges': [(0, 2), (0, 4)], 'dim': 2, 'nbins': [2, 2]}}
        )]
