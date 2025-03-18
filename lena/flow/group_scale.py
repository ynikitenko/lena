"""Scale a group of data."""
import numbers

import lena.core
import lena.flow


def scale_to(scale_to, group,
             allow_zero_scale=False, allow_unknown_scale=False):
    """Scale each structure in a *group*.

    The group is a sequence of *(structure, context)* pairs
    (not the result of :func:`group_plots`!).
    Each structure must have a method *scale*.
    The original group is rescaled in place.

    If any item could not be rescaled and
    the options were not set to ignore that,
    :exc:`.LenaValueError` is raised.
    See the documentation for :class:`GroupScale` for details
    on *allow_zero_scale* and *allow_unknown_scale*.
    """
    if isinstance(scale_to, numbers.Number):
        scale = scale_to
    else:
        # get scale to be used
        scale_to = lena.flow.Selector(scale_to)
        cands = [val for val in group if scale_to(val)]
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
            if not allow_unknown_scale:
                raise lena.core.LenaValueError(
                    "could not determine the scale of {}"
                    .format(val)
                )
        except lena.core.LenaValueError as err:
            # scale is zero and can't be changed
            if not allow_zero_scale:
                raise err
    return None


class GroupScale(object):
    """Scale a group of data."""

    def __init__(self, scale_to,
                 allow_zero_scale=False, allow_unknown_scale=False):
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

        .. hint ::
            To scale only one value, use
            :class:`lena.structures.ScaleTo <lena.structures.elements.ScaleTo>`.
        """
        self._scale_to = scale_to
        self._allow_zero_scale = allow_zero_scale
        self._allow_unknown_scale = allow_unknown_scale

    def __call__(self, group):
        """Scale the group. See :func:`scale_to` for details.

        If *group* is not iterable, :exc:`.LenaValueError` is raised.
        """
        if not isinstance(group, (list, tuple)):
            raise lena.core.LenaValueError(
                "value must be a list or other materialized iterable"
            )
        scale_to(self._scale_to, group,
                 self._allow_zero_scale, self._allow_unknown_scale)
        return group
