class DataPath():
    def __call__(self):
        paths = ["normal_3d.csv"]
        for path in paths:
            # maybe add context that it is data.
            yield path
