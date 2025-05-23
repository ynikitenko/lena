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
    gr0  = graph([[0, 1], [2.5, 3]])
    to_csv = ToCSV(separator=",", header=None, duplicate_last_bin=True)

    ## histogram and iterables work, other values passed unchanged
    # no context works fine
    res0 = list(to_csv.run([hist, gr0, 3, "a string"]))
    # data parts are correct
    data_0 = [res0[0][0], res0[1][0]]
    assert data_0 == [
        '0.000000,1.000000\n1.000000,2.000000\n2.000000,2.000000',
        '0,2.5\n1,3',
    ]
    # other values are skipped
    assert res0[2:] == [3, "a string"]
    ## histogram context part is correct
    # get it directly from histogram in order not to mix with this test
    hist_cont = {}
    hist._update_context(hist_cont)
    hist_cont.update({'output': {'filetype': 'csv'}})
    assert res0[0][1] == hist_cont
    # something like
    # {
    #     'histogram': {'dim': 1, 'nbins': [2], 'ranges': [(0, 2)],
    #                   'n_out_of_range': 0},
    #     'output': {'filetype': 'csv'}
    # }
    # graph context part has no error fields
    assert res0[1][1] == {'output': {'filetype': 'csv'}}

    # data._update_context is called for not histograms
    gr1 = graph([[0, 1], [2.5, 3], [0.1, 0.1]], field_names="x,y,error_y")
    res1 = list(to_csv.run([gr1]))[0]
    assert res1[1] == {
        'output': {'filetype': 'csv'},
        'error': {'y': {'index': 2}}
    }

    # context.to_csv.False forbids the transform
    no_to_csv_context = {"output": {"to_csv": False}}
    res2 = list(to_csv.run([(gr0, no_to_csv_context)]))[0]
    assert res2 == (gr0, no_to_csv_context)

    to_csv_re = ToCSV(separator=",", row_end="\\", header=None,
                      duplicate_last_bin=True)
    res_re = list(to_csv_re.run([hist]))
    csv_re = res_re[0][0]
    assert csv_re == "0.000000,1.000000\\\n1.000000,2.000000\\\n2.000000,2.000000"
    to_csv_lre = ToCSV(
        separator=",", row_end="\\", last_row_end="\\\n", header=None,
        duplicate_last_bin=True
    )
    res_lre = list(to_csv_lre.run([hist]))
    assert res_lre[0][0] == csv_re + "\\\n"


def test_hist_to_csv():
    ## histogram functions work
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

    hist = histogram(edges=[[0, 1, 2], [0, 2, 4]], bins=[[1, 2], [3, 4]])
    assert list(hist2d_to_csv(hist)) == [
            '0.000000,0.000000,1.000000', '0.000000,2.000000,2.000000', '0.000000,4.000000,2.000000', '1.000000,0.000000,3.000000', '1.000000,2.000000,4.000000', '1.000000,4.000000,4.000000', '2.000000,0.000000,3.000000', '2.000000,2.000000,4.000000', '2.000000,4.000000,4.000000']
    assert list(hist2d_to_csv(hist, header='x,y,z')) == [
            'x,y,z', '0.000000,0.000000,1.000000', '0.000000,2.000000,2.000000', '0.000000,4.000000,2.000000', '1.000000,0.000000,3.000000', '1.000000,2.000000,4.000000', '1.000000,4.000000,4.000000', '2.000000,0.000000,3.000000', '2.000000,2.000000,4.000000', '2.000000,4.000000,4.000000']
    assert list(hist2d_to_csv(hist, duplicate_last_bin=False)) == [
            '0.000000,0.000000,1.000000', '0.000000,2.000000,2.000000', '1.000000,0.000000,3.000000', '1.000000,2.000000,4.000000']
    assert list(hist2d_to_csv(hist, separator=' ')) == [
            '0.000000 0.000000 1.000000', '0.000000 2.000000 2.000000', '0.000000 4.000000 2.000000', '1.000000 0.000000 3.000000', '1.000000 2.000000 4.000000', '1.000000 4.000000 4.000000', '2.000000 0.000000 3.000000', '2.000000 2.000000 4.000000', '2.000000 4.000000 4.000000']

    ## ToCSV element works
    hist = Histogram(edges=[0, 1, 2], bins=[1, 2])
    to_csv = ToCSV()
    hist_data = list(hist.compute())
    res0 = list(to_csv.run(hist_data))
    assert len(res0) == 1
    assert res0[0][0] == '0.000000,1.000000\n1.000000,2.000000\n2.000000,2.000000'

    ## maybe redundant
    to_csv = ToCSV(duplicate_last_bin=False)
    hist_el = Histogram(edges=[[0, 1, 2], [0, 2, 4]], bins=[[1, 2], [3, 4]])
    hist_data = list(hist_el.compute())
    res1 = list(to_csv.run(hist_data))
    assert res1[0][0] == (
        '0.000000,0.000000,1.000000\n0.000000,2.000000,2.000000\n1.000000,0.000000,3.000000\n1.000000,2.000000,4.000000'
    )
