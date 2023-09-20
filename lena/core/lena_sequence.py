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
        from lena.context import update_recursively
        # todo: this doesn't require jinja2,
        # but we may want it to support template strings soon
        self._seq = args
        seq = []

        # for static (sequence initialisation time) context
        need_context = []
        unknown_contexts = []
        context = {}

        # get static context.
        # External/earlier context takes precedence.
        for el in reversed(args):
            # we don't check whether they are callable here,
            # because otherwise there will be an error
            # during initialisation (not runtime)
            if hasattr(el, "_unknown_contexts"):
                # we don't expand in place even if we could,
                # because external/top context has priority
                unknown_contexts.extend(el._unknown_contexts)
            if hasattr(el, "_get_context"):
                el_context = el._get_context()
                update_recursively(context, el_context)

        # Render that context that we can. Context is updated.
        _update_unknown_contexts(unknown_contexts, context)
        # unknown_contexts of this sequence are left as they are.
        # We shall set them every time we update context.
        # unknown_contexts = _update_unknown_contexts(unknown_contexts, context)
        # There is no way to check (during init)
        # that all static context was set,
        # because sequences are allowed to separate/wrap any elements.

        for el in args:
            # orders of setters and getters are independent:
            # context is same for the whole sequence
            # (and external ones, but not for Split)
            if hasattr(el, "_set_context"):
                # if not unknown_contexts:
                # we set context after all unknowns are known.
                # el can't have unknown contexts
                # (except subsequences of Split);
                # at least not contexts
                # that shall update the current context
                el._set_context(context)
                need_context.append(el)

            # todo 0.7: or has context
            if not hasattr(el, "_has_no_data"):
                seq.append(el)

        self._context = context
        self._unknown_contexts = unknown_contexts
        self._need_context = need_context

        self._data_seq = seq

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
        from lena.context import update_recursively
        # parent context doesn't necessarily has our context
        # (for example, when we are inside Split).
        # We update current context with context.
        update_recursively(self._context, context)
        if hasattr(self, "_unknown_contexts"):
            # Can be empty, this is fine.
            # We don't update context with those rendered here,
            # because we can be in Split. All common unknown contexts
            # have already updated the common context.
            # We update the current context, however.
            _update_unknown_contexts(self._unknown_contexts[:],
                                     self._context)
            # containing Sequence may redefine some values,
            # therefore we need to set unknown_contexts each time;
            # however, we no longer update the external context.
            # if unknown_contexts:
            #     self._unknown_contexts = unknown_contexts
            #     # don't set context for other elements
            #     # until all contexts are known
            #     return
            # else:
            #     del self._unknown_contexts
        for el in self._need_context:
            el._set_context(self._context)

    def _get_context(self):
        return deepcopy(self._context)
