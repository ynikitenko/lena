class ReadData():
    """Read data from CSV files."""

    def run(self, flow):
        """Read filenames from flow and yield vectors.

        If vector component could not be cast to float,
        *ValueError* is raised.
        """
        for filename in flow:
            with open(filename, "r") as fil:
                for line in fil:
                    vec = [float(coord)
                           for coord in line.split(',')]
                    yield vec


class ReadDoubleEvents():
    """Read data from CSV files."""

    def run(self, flow):
        """Read filenames from flow and yield double events.

        If vector component could not be cast to float,
        *ValueError* is raised.
        """
        for filename in flow:
            with open(filename, "r") as fil:
                first_ev = None
                for line in fil:
                    event = [float(coord)
                           for coord in line.split(',')]
                    if first_ev is None:
                        first_ev = event
                    else:
                        yield (first_ev, event)
                        first_ev = None
