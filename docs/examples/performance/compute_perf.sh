{
    echo \# Lena commit: `git log --pretty=format:'%h' -n 1`, `python -V`
    # It's meaningful to not produce plots (because we don't measure pdflatex performance).
    # But it's safe to "produce" them in code if they exist: they won't be reproduced!
    # Disk cache seems not relevant, because the times don't change much between runs
    # (and time of pure read is very very small)
    #
    echo \# one histogram:
    /bin/time python lena_xs.py 2>&1 >/dev/null
    echo \# Split, two histograms:
    /bin/time python lena_xy.py 2>&1 >/dev/null
} >> performance.txt
# feel free to add meaningful comments to performance.txt!
#
# anonymous function trick taken from https://stackoverflow.com/a/315113/952234
# help with redirection from https://stackoverflow.com/a/549776/952234
