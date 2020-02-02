import os
from matplotlib import pyplot as plt


def read_data(filename):
    data = []
    with open(filename) as fil:
        for line in fil:
            data.append(float(line))
    return data


filename = os.path.join("..", "data", "x.csv")
data = read_data(filename)
average = sum(data) / len(data)
plt.hist(data, bins=5, range=[-10, 10])
plt.savefig(os.path.join("output", "just_x.png"))
