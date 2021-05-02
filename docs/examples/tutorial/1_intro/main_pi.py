from __future__ import print_function

import lena.flow
from lena.core import Sequence, Source


class Sum():
    def run(self, flow):
        s = 0
        for val in flow:
            s += val
        yield s


def main():
    s = Sequence(
        lambda i: pow(-1, i) * (2 * i + 1),
    )
    results = s.run([0, 1, 2, 3])
    for res in results:
        print(res, end=" ")
    # 1 -3 5 -7 
    # 
    # s0 = Source(
    #     lena.flow.CountFrom(0),
    #     s,
    #     lena.flow.Slice(5),
    # )
    # results = s0()
    # print(list(results))
    spi = Source(
        lena.flow.CountFrom(0),
        s,
        lena.flow.Slice(10**6),
        lambda x: 4./x,
        Sum(),
    )
    results = list(spi())
    print(results)
    # [3.1415916535897743]
    return results


if __name__ == "__main__":
    main()
