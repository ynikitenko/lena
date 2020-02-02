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
                    yield (vec, {"data": {"filename": filename}})
