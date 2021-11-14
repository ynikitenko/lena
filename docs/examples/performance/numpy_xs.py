import os
import numpy
from matplotlib import pyplot as plt


def plot_data():
    data_path = os.path.join("..", "tutorial", "data")
    data_file = os.path.join(data_path, "normal_3d_large.csv")
    use_np_load = False

    if use_np_load:
        # The recommended way of plotting data from a file is ...
        # numpy.loadtxt or pandas.read_csv to read the data.
        # These are more powerful and faster.
        # https://matplotlib.org/3.2.2/gallery/misc/plotfile_demo_sgskip.html
        data = numpy.loadtxt(data_file, delimiter=',', usecols=0)
        # /bin/time, without savefig
        # 2.94user 0.30system 0:03.00elapsed 107%CPU (0avgtext+0avgdata 117196maxresident)k
        # 0inputs+0outputs (0major+19994minor)pagefaults 0swaps
    else:
        filenames = [data_file]
        data = []
        for filename in filenames:
            with open(filename) as fil:
                for line in fil:
                    data.append(float(line.split(',')[0]))
        # /bin/time, without savefig
        # 3.11user 0.33system 0:03.17elapsed 108%CPU (0avgtext+0avgdata 437396maxresident)k
        # 0inputs+0outputs (0major+97214minor)pagefaults 0swaps

    plt.hist(data, bins=100, range=[-10, 10])
    # plt.savefig(os.path.join("output", "pyplot_xs.png"))


if __name__ == "__main__":
    plot_data()


## Educational notes. Examples were not tested and are not used.

# "Top-down"

def td_read_files(filenames, data):
    for filename in filenames:
        with open(filename) as fil:
            for line in fil:
                data.append(td_read_line(line))


def td_read_line(line):
    """Return x column"""
    return float(line.split(',')[0])


# "Bottom-up"

def get_filenames():
    filenames = []
    for filename in filenames:
        yield filename

def bu_read_lines():
    # or get data as an argument
    data = []
    for filename in get_filenames():
        with open(filename) as fil:
            for line in fil:
                data.append(float(line.split(',')[0]))
    return data


## note the coupling between these functions
