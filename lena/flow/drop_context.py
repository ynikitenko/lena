from lena.core.sequence import Sequence
from lena.flow.functions import _has_context


class DropContext():
    """Sequence, which transform *(data, context)* flow
    so that only *data* remains in the inner sequence.
    Context is restored outside *DropContext*.

    *DropContext* works for most simple cases as a *Sequence*,
    but may not work in more advanced circumstances.
    For example, since *DropContext* is not transparent,
    :class:`Split` can't judge
    whether it has a *FillCompute* element inside,
    and this may lead to errors in the analysis.
    It is recommended to provide *context* when possible.
    """
    # probably, this is in important element, since dealing with context
    # and deepcopy takes relatively much time.
    # Lena elements should probably have methods like fill_data,
    # run_data (?), compute_data, request_data,
    # and make_context(self, other_context).
    # This may be added in future versions.
    # todo: add methods from the inner sequences, add tests.
    def __init__(self, *args):
        """*\*args* will form a :class:`Sequence`.
        """
        self.sequence = Sequence(*args)
        self.cur_context = None

    def _make_iterator(self, iterable):
        for data, context in iterable:
            self.cur_context = context
            yield data

    def run(self, flow):
        """Run the sequence without context,
        and generate output flow restoring the context
        before *DropContext*.

        If the sequence adds a context,
        the returned context is updated with that.
        """
        dcit = self._make_iterator(flow)
        results_iter = self.sequence.run(dcit)

        for result in results_iter:
            context = self.cur_context
            # Update context if self.sequence created that.
            if _has_context(result):
                new_context = result[1]
                result = result[0]
                context.update(new_context)
            yield (result, context)
