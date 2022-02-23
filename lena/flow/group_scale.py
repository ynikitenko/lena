"""Scale a group of data."""
import numbers

import lena.core
import lena.flow


class GroupScale(object):
    """Scale a group of data."""

    def __init__(self, scale_to, allow_zero_scale=False, allow_unknown_scale=False):
        """*scale_to* defines the method of scaling.
        If a number is given, group items are scaled to that.
        Otherwise it is converted to a :class:`.Selector`,
        which must return a unique item from the group.
        Group items will be scaled to the scale of that item.

        By default, attempts to rescale a structure
        with unknown or zero scale raise an error.
        If *allow_zero_scale* and *allow_unknown_scale*
        are set to ``True``,
        the corresponding errors are ignored
        and the structure remains unscaled.
        """
        if isinstance(scale_to, numbers.Number):
            self._scale_to = scale_to
        else:
            self._scale_to = lena.flow.Selector(scale_to)
        self._allow_zero_scale = allow_zero_scale
        self._allow_unknown_scale = allow_unknown_scale

    def scale(self, group):
        """Scale each structure in a *group*.

        The *group* can contain *(structure, context)* pairs.
        The original group is rescaled in place.

        If any item could not be rescaled and
        options were not set to ignore that,
        :exc:`.LenaValueError` is raised.
        """
        # get scale to be used
        if isinstance(self._scale_to, numbers.Number):
            scale = self._scale_to
        else:
            cands = [val for val in group if self._scale_to(val)]
            if len(cands) > 1:
                raise lena.core.LenaValueError(
                    "only one candidate to provide scale must be selected, "
                    "{} found".format(cands)
                )
            elif not cands:
                raise lena.core.LenaValueError(
                    "at least one item to get scale from must be selected"
                )
            else:
                cand = cands[0]
            scale = lena.flow.get_data(cand).scale()

        # rescale
        for val in group:
            data, context = lena.flow.get_data_context(val)
            try:
                data.scale(scale)
            except AttributeError as err:
                # scale was not set and can't be determined
                if not self._allow_unknown_scale:
                    raise lena.core.LenaValueError(
                        "could not determine the scale of {}"
                        .format(val)
                    )
            except lena.core.LenaValueError as err:
                # scale is zero and can't be changed
                if not self._allow_zero_scale:
                    raise err
        return None
