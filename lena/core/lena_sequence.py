"""LenaSequence abstract base class."""
from copy import deepcopy

import lena.context


def _update_unknown_contexts(unknown_contexts, context):
    """Update values in *unknown_contexts* from *context*
    and update *context* with the new values.
    """
    from lena.context import (
        format_context, str_to_dict, update_recursively
    )
    new_unknowns = []
    for uc in unknown_contexts:
        key, value = uc
        fc = format_context(value)
        try:
            rendered = fc(context)
        except lena.core.LenaKeyError:
            new_unknowns.append(uc)
        else:
            rendered_context = str_to_dict(key, rendered)
            update_recursively(context, rendered_context)

    # if we could render something, try to render other elements
    # with the updated context
    if len(new_unknowns) != len(unknown_contexts):
        new_unknowns = _update_unknown_contexts(new_unknowns, context)

    return new_unknowns


class LenaSequence(object):
    """Abstract base class for all Lena sequences.

    A sequence consists of elements.
    *LenaSequence* provides methods to iterate over a sequence,
    get its length and get an item at the given index.
    """
    def __init__(self, *args):
        self._seq = args
        data_seq  = []
        with_static_context = []

        for el in args:
            # That would be bad design because of action at a distance,
            # or, more precise, lack of causality (1-directionality).
            # # orders of setters and getters are independent:
            # # context is same for the whole sequence
            # # (and external ones, but not for Split)

            # todo v0.7: if _has_context
            if not hasattr(el, "_has_no_data"):
                data_seq.append(el)

            if hasattr(el, "_get_context") or hasattr(el, "_set_context"):
                with_static_context.append(el)

        self._data_seq = data_seq
        # copied from meta.SetContext
        try:
            self._set_context({})
        except LenaKeyError:
            pass

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

    def __eq__(self, other):
        if not isinstance(other, LenaSequence):
            return NotImplemented
        return self._seq == other._seq

    def __repr__(self):
        # maybe: make a compact representation with repr
        # and nested with str
        return self._repr_nested()

    def _set_context(self, context):
        """Set static context based on the external *context*."""
        # Context must pass through every element of this sequence,
        # since it not only updates context,
        # but can also delete that (via Split).
        # No optimisation for future contexts is possible.

        # todo: get context only when necessary. Change the order.
        # We could economise last _get_context here.
        # For example, if the last element is a big Split, whose
        # static context we don't need to know any more (it is the end).

        for el in self._seq:
            if hasattr(el, "_set_context") and context:
                # skip empty context as an optimisation
                # (el could be a big sequence).
                # Every element with _set_context
                # sets the empty context during its initialisation.
                try:
                    el._set_context(context)
                except LenaKeyError:
                    # needed keys are lacking in the context.
                    # _static_context is not set.
                    # If _static_context was already set,
                    # we won't be here, since external context
                    # can not delete local keys.
                    return

            if hasattr(el, "_get_context"):
                # every element that has _get_context
                # must also have _set_context
                context = el._get_context()

        self._static_context = context

    def _get_context(self):
        # copied from meta.SetContext
        try:
            sc = self._static_context
        except AttributeError:
            raise LenaAttributeError(
                "static context missing. Run _set_context to set that."
            )
        return deepcopy(sc)
