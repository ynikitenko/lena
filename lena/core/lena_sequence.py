"""LenaSequence abstract base class."""


class LenaSequence(object):
    """Abstract base class for all Lena sequences.

    A sequence consists of elements.
    *LenaSequence* provides methods to iterate over a sequence,
    get its length and get an item at the given index.
    """
    def __init__(self, *args):
        self._seq = args

    def __iter__(self):
        return self._seq.__iter__()

    def __len__(self):
        return self._seq.__len__()

    def __getitem__(self, ind):
        return self._seq[ind]

    def _repr_nested(self, base_indent="", indent=" "*4, el_separ=",\n"):
        # to get a one-line representation, use el_separ=", ", indent=""

        def repr_maybe_nested(el, base_indent, indent):
            if hasattr(el, "_repr_nested"):
                return el._repr_nested(base_indent=base_indent+indent, indent=indent)
            else:
                return base_indent + indent + repr(el)

        elems = el_separ.join((repr_maybe_nested(el, base_indent=base_indent,
                                                 indent=indent)
                               for el in self._seq))

        if "\n" in el_separ and self._seq:
            # maybe new line
            mnl = "\n"
            # maybe base indent
            mbi = base_indent
        else:
            mnl = ""
            mbi = ""
        return "".join([base_indent, self._name,
                        "(", mnl, elems, mnl, mbi, ")"])

    def __repr__(self):
        # maybe: make a compact representation with repr
        # and nested with str
        return self._repr_nested()
