"""LenaSequence abstract base class."""
from copy import deepcopy

import lena.context


class LenaSequence(object):
    """Abstract base class for all Lena sequences.

    A sequence consists of elements.
    *LenaSequence* provides methods to iterate over a sequence,
    get its length and get an item at the given index.
    """
    def __init__(self, *args):
        # todo: this doesn't require jinja2,
        # but we may want it to support template strings soon
        from lena.context import update_recursively
        self._full_seq = args
        seq = []

        # for static (sequence initialisation time) context
        need_context = []
        context = {}

        # get static context.
        # External/earlier context takes precedence.
        for el in reversed(args):
            # we don't check whether they are callable here,
            # because otherwise there will be an error
            # during initialisation (not runtime)
            if hasattr(el, "_get_context"):
                # todo: allow template substitution
                update_recursively(context, el._get_context())

        for el in args:
            # orders of setters and getters are independent:
            # context is same for the whole sequence
            # (and external ones, but not for Split)
            if hasattr(el, "_set_context"):
                el._set_context(context)
                need_context.append(el)

            # todo: or has context
            if not hasattr(el, "_has_no_data"):
                seq.append(el)

        self._context = context
        self._need_context = need_context

        self._seq = seq

    def __iter__(self):
        return self._full_seq.__iter__()

    def __len__(self):
        return self._full_seq.__len__()

    def __getitem__(self, ind):
        return self._full_seq[ind]

    def _repr_nested(self, base_indent="", indent=" "*4, el_separ=",\n"):
        # to get a one-line representation, use el_separ=", ", indent=""

        def repr_maybe_nested(el, base_indent, indent):
            if hasattr(el, "_repr_nested"):
                return el._repr_nested(base_indent=base_indent+indent, indent=indent)
            else:
                return base_indent + indent + repr(el)

        elems = el_separ.join((repr_maybe_nested(el, base_indent=base_indent,
                                                 indent=indent)
                               for el in self._full_seq))

        if "\n" in el_separ and self._full_seq:
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

    def _set_context(self, context):
        for el in self._need_context:
            # we don't use self._context,
            # because it was already set in this seq.
            el._set_context(context)

    def _get_context(self):
        return deepcopy(self._context)
