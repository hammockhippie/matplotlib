import itertools


def check_in_list(_values, *, _print_supported_values=True, **kwargs):
    """
    For each *key, value* pair in *kwargs*, check that *value* is in *_values*.

    Parameters
    ----------
    _values : iterable
        Sequence of values to check on.
    _print_supported_values : bool, default: True
        Whether to print *_values* when raising ValueError.
    **kwargs : dict
        *key, value* pairs as keyword arguments to find in *_values*.

    Raises
    ------
    ValueError
        If any *value* in *kwargs* is not found in *_values*.

    Examples
    --------
    >>> _api.check_in_list(["foo", "bar"], arg=arg, other_arg=other_arg)
    """
    values = _values
    for key, val in kwargs.items():
        if val not in values:
            if _print_supported_values:
                raise ValueError(
                    f"{val!r} is not a valid value for {key}; "
                    f"supported values are {', '.join(map(repr, values))}")
            else:
                raise ValueError(f"{val!r} is not a valid value for {key}")


def check_shape(_shape, **kwargs):
    """
    For each *key, value* pair in *kwargs*, check that *value* has the shape
    *_shape*, if not, raise an appropriate ValueError.

    *None* in the shape is treated as a "free" size that can have any length.
    e.g. (None, 2) -> (N, 2)

    The values checked must be numpy arrays.

    Examples
    --------
    To check for (N, 2) shaped arrays

    >>> _api.check_shape((None, 2), arg=arg, other_arg=other_arg)
    """
    target_shape = _shape
    for k, v in kwargs.items():
        data_shape = v.shape

        if len(target_shape) != len(data_shape) or any(
                t not in [s, None]
                for t, s in zip(target_shape, data_shape)
        ):
            dim_labels = iter(itertools.chain(
                'MNLIJKLH',
                (f"D{i}" for i in itertools.count())))
            text_shape = ", ".join((str(n)
                                    if n is not None
                                    else next(dim_labels)
                                    for n in target_shape))

            raise ValueError(
                f"{k!r} must be {len(target_shape)}D "
                f"with shape ({text_shape}). "
                f"Your input has shape {v.shape}."
            )


def check_getitem(_mapping, **kwargs):
    """
    *kwargs* must consist of a single *key, value* pair.  If *key* is in
    *_mapping*, return ``_mapping[value]``; else, raise an appropriate
    ValueError.

    Examples
    --------
    >>> _api.check_getitem({"foo": "bar"}, arg=arg)
    """
    mapping = _mapping
    if len(kwargs) != 1:
        raise ValueError("check_getitem takes a single keyword argument")
    (k, v), = kwargs.items()
    try:
        return mapping[v]
    except KeyError:
        raise ValueError(
            "{!r} is not a valid value for {}; supported values are {}"
            .format(v, k, ', '.join(map(repr, mapping)))) from None
