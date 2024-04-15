from lena.core import LenaValueError


def _group_by_starting_prefixes(keys):
    """Group *keys* by common starting prefixes.

    *keys* is a list of key tuples.
    The starting prefix is the first element of the key tuple,
    while the rest is its tail.

    Returns a dictionary of key prefixes
    to lists of tails of keys with those starting prefixes.
    """
    # every key returned by _split_key is non-empty.
    assert all(key for key in keys)
    start_prefixes = set(key[0] for key in keys)

    gbsp = {sp: [] for sp in start_prefixes}
    for key in keys:
        gbsp[key[0]].append(key[1:])

    return gbsp


def _split_key(key):
    """Split *key* into subkeys separated by dots.

    All subkeys must be proper, that is
    empty ones are not allowed (examples of improper subkeys are
    "a..b" or ".a"). Improper subkeys raise :exc:`.LenaValueError`.
    """
    # todo: what is the difference with str_to_list?
    # Probably only error checks.
    if key == "":
        # return a list since split returns a list
        return [key]

    skey = key.split('.')
    if "" in skey:
        raise LenaValueError(
            "Improper subkey found in '{}'.\n".format(key) +
            "Make sure that every dot is surrounded by non-dots."
        )
    return skey


def _startswith(s1, s2):
    """Test whether a container *s2* starts with *s1*."""
    # For strings one could also use os.path.commonprefix
    # or str.startswith .
    # len is a const operation for usual Python containers.
    if len(s2) < len(s1):
        return False

    for ind, sk in enumerate(s1):
        if s2[ind] != sk:
            return False

    return True


class IncludeExcludeTree():
    """A tree to get parts of a dictionary according to
    the rules of inclusion and exclusion.
    """

    def __init__(self, keys, subtrees, include):
        """*keys* is a set of flat strings.
        Their usage depends on *include*: if it is ``True``,
        then this tree includes by default and the explicit *keys*
        should be *excluded* in :meth:`get`. Otherwise the keys
        should be included.

        *subtrees* is a mapping from string keys
        to actual include-exclude trees.
        If a subtree has no other subtrees of its own,
        its *include* must be different from that of this tree.
        """
        self.keys = keys
        self.subtrees = subtrees
        self.include = bool(include)

        # to be done.
        # For now nested substrings of the same type are checked
        # during _make_include_exclude_tree, but this could also
        # be checked in the tree (as its invariant).
        # However, this invariant is hard to formulate.
        # # check subtrees correctness
        # for st in subtrees.values():
        #     if st.keys:
        #         for sst in st.subtrees.values():
        #             # It was a key in includes or excludes.
        #             # Change the default in its daughters.
        #             if sst.subtrees:
        #                 assert sst.include == (not include)

    def get(self, context):
        """Get parts of a dictionary *context*
        corresponding to this tree.

        Corresponds (is dual) to *dict.get(key)*.
        """
        result = {}
        if self.include:
            # by default include
            exclude = self.keys
            for key, value in context.items():
                if key in exclude:
                    continue
                elif key in self.subtrees:
                    if isinstance(value, dict):
                        # otherwise it won't be selected anyway
                        result[key] = self.subtrees[key].get(value)
                else:
                    result[key] = value
        else:
            # by default exclude
            include = self.keys
            for key, value in context.items():
                if key in include:
                    result[key] = value
                elif key in self.subtrees:
                    if isinstance(value, dict):
                        # otherwise it won't be selected
                        result[key] = self.subtrees[key].get(value)
                else:
                    continue

        return result

    def __eq__(self, other):
        if not isinstance(other, IncludeExcludeTree):
            return NotImplemented
        return (self.keys == other.keys and self.subtrees == other.subtrees and
                self.include == other.include)

    def __repr__(self):
        return "IncludeExcludeTree(keys={}, subtrees={}, include={})"\
                .format(self.keys, self.subtrees, self.include)


def _make_include_exclude_tree(includes, excludes, is_default_include):
    """*includes* and *excludes* are lists of keys,
    which are tuples of subkeys.

    *is_default_include* defines the default behaviour for
    not explicitly given keys.
    """
    # returns a dict {first: [tails]}
    pref_excs = _group_by_starting_prefixes(excludes)
    pref_incs = _group_by_starting_prefixes(includes)

    if is_default_include:
        # the next nested level are excludes, and then again includes
        extra_keys = set(pref_incs.keys()).difference(set(pref_excs.keys()))
    else:
        extra_keys = set(pref_excs.keys()).difference(set(pref_incs.keys()))
    if extra_keys:
        raise LenaValueError(
            "Remove extra subkeys. "
            "Include/exclude keys should be strictly within "
            "exclude/include keys respectively.\n"
            "Hint: see intermediate prefixes {}".format(extra_keys)
        )

    # proper means not subtrees
    proper_keys = set()
    subtrees = {}

    if is_default_include:
        subkeys = pref_excs
        subsubs = pref_incs
    else:
        subkeys = pref_incs
        subsubs = pref_excs

    for key, tails in subkeys.items():
        # (key, tails) form a full key. key is its start,
        # and tails is the remainder of the key.
        if tails == [[]] and key not in subsubs:
            proper_keys.add(key)
        else:
            if min(len(subkey) for subkey in tails) == 0:
                # A new "" encountered.
                # Here it is important that includes/excludes
                # are properly nested, or we would get a bug here.
                # And this will be checked in a recursive call
                # with a new default include.
                new_incl = (not is_default_include)
            else:
                # A key "c.d.e" won't change inclusion for "c.*".
                new_incl = is_default_include

            includes = [sk for sk in pref_incs.get(key, []) if sk]
            excludes = [sk for sk in pref_excs.get(key, []) if sk]
            subtrees[key] = _make_include_exclude_tree(
                includes=includes,
                excludes=excludes,
                is_default_include=new_incl
            )

    return IncludeExcludeTree(
        keys=proper_keys, subtrees=subtrees, include=is_default_include
    )


def make_include_exclude_tree(includes=tuple(), excludes=tuple()):

    # make arguments tuples for generality
    if isinstance(includes, str):
        includes = (includes,)
    if isinstance(excludes, str):
        excludes = (excludes,)

    is_default_include = "" in includes
    if is_default_include + ("" in excludes) != 1:
        raise LenaValueError(
            "The root (empty) string must be contained in exactly one "
            "of include or exclude sets."
        )

    sincs = [_split_key(key) for key in includes if key != ""]
    sexcs = [_split_key(key) for key in excludes if key != ""]

    iet = _make_include_exclude_tree(
        includes=sincs, excludes=sexcs, is_default_include=is_default_include
    )
    return iet
