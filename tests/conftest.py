try:
    import ROOT
except ImportError:
    collect_ignore_glob = ["*/root/*"]
    # otherwise will have problems either with tox,
    # or when executing pytest directly
    collect_ignore_glob += ["root/*"]
