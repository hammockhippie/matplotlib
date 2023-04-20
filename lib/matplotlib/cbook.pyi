import collections.abc
from collections.abc import Callable, Collection, Generator, Iterable, Iterator
import contextlib
import os
from pathlib import Path

from matplotlib.artist import Artist

import numpy as np
from numpy.typing import ArrayLike

from typing import (
    Any,
    ContextManager,
    Generic,
    IO,
    Literal,
    TypeVar,
    overload,
)

_T = TypeVar("_T")

class CallbackRegistry:
    exception_handler: Callable[[Exception], Any]
    callbacks: dict[Any, dict[int, Any]]
    def __init__(
        self,
        exception_handler: Callable[[Exception], Any] | None = ...,
        *,
        signals: Iterable[Any] | None = ...
    ) -> None: ...
    def connect(self, signal: Any, func: Callable) -> int: ...
    def disconnect(self, cid: int) -> None: ...
    def process(self, s: Any, *args, **kwargs) -> None: ...
    @contextlib.contextmanager
    def blocked(self, *, signal: Any | None = ...): ...

class silent_list(list[_T]):
    type: str | None
    def __init__(self, type, seq: Iterable[_T] | None = ...) -> None: ...

def strip_math(s: str) -> str: ...
def is_writable_file_like(obj: Any) -> bool: ...
def file_requires_unicode(x: Any) -> bool: ...
@overload
def to_filehandle(
    fname: str | os.PathLike | IO,
    flag: str = ...,
    return_opened: Literal[False] = ...,
    encoding: str | None = ...,
) -> IO: ...
@overload
def to_filehandle(
    fname: str | os.PathLike | IO,
    flag: str,
    return_opened: Literal[True],
    encoding: str | None = ...,
) -> tuple[IO, bool]: ...
@overload
def to_filehandle(
    fname: str | os.PathLike | IO,
    *, # if flag given, will match previous sig
    return_opened: Literal[True],
    encoding: str | None = ...,
) -> tuple[IO, bool]: ...
def open_file_cm(
    path_or_file: str | os.PathLike | IO,
    mode: str = ...,
    encoding: str | None = ...,
) -> ContextManager[IO]: ...
def is_scalar_or_string(val: Any) -> bool: ...
@overload
def get_sample_data(
    fname: str | os.PathLike,
    asfileobj: Literal[True] = ...,
    *,
    np_load: Literal[True]
) -> np.ndarray: ...
@overload
def get_sample_data(
    fname: str | os.PathLike,
    asfileobj: Literal[True] = ...,
    *,
    np_load: Literal[False] = ...
) -> IO: ...
@overload
def get_sample_data(
    fname: str | os.PathLike,
    asfileobj: Literal[False],
    *,
    np_load: bool = ...
) -> str: ...
def _get_data_path(*args: Path | str) -> Path: ...
def flatten(
    seq: Iterable[Any], scalarp: Callable[[Any], bool] = ...
) -> Generator[Any, None, None]: ...

class Stack(Generic[_T]):
    def __init__(self, default: _T | None = ...) -> None: ...
    def __call__(self) -> _T: ...
    def __len__(self) -> int: ...
    def __getitem__(self, ind: int) -> _T: ...
    def forward(self) -> _T: ...
    def back(self) -> _T: ...
    def push(self, o: _T) -> _T: ...
    def home(self) -> _T: ...
    def empty(self) -> bool: ...
    def clear(self) -> None: ...
    def bubble(self, o: _T) -> _T: ...
    def remove(self, o: _T) -> None: ...

def safe_masked_invalid(x: ArrayLike, copy: bool = ...) -> np.ndarray: ...
def print_cycles(
    objects: Iterable[Any], outstream: IO = ..., show_progress: bool = ...
) -> None: ...

class Grouper(Generic[_T]):
    def __init__(self, init: Iterable[_T] = ...) -> None: ...
    def __contains__(self, item: _T) -> bool: ...
    def clean(self) -> None: ...
    def join(self, a: _T, *args: _T) -> None: ...
    def joined(self, a: _T, b: _T) -> bool: ...
    def remove(self, a: _T) -> None: ...
    def __iter__(self) -> Iterator[list[_T]]: ...
    def get_siblings(self, a: _T) -> list[_T]: ...

class GrouperView(Generic[_T]):
    def __init__(self, grouper: Grouper[_T]) -> None: ...
    def __contains__(self, item: _T) -> bool: ...
    def __iter__(self) -> Iterator[list[_T]]: ...
    def joined(self, a: _T, b: _T) -> bool: ...
    def get_siblings(self, a: _T) -> list[_T]: ...

def simple_linear_interpolation(a: ArrayLike, steps: int) -> np.ndarray: ...
def delete_masked_points(*args): ...
def boxplot_stats(
    X: ArrayLike,
    whis: float | tuple[float, float] = ...,
    bootstrap: int | None = ...,
    labels: ArrayLike | None = ...,
    autorange: bool = ...,
) -> list[dict[str, Any]]: ...

ls_mapper: dict[str, str]
ls_mapper_r: dict[str, str]

def contiguous_regions(mask: ArrayLike) -> list[np.ndarray]: ...
def is_math_text(s: str) -> bool: ...
def violin_stats(
    X: ArrayLike, method: Callable, points: int = ..., quantiles: ArrayLike | None = ...
) -> list[dict[str, Any]]: ...
def pts_to_prestep(x: ArrayLike, *args: ArrayLike) -> np.ndarray: ...
def pts_to_poststep(x: ArrayLike, *args: ArrayLike) -> np.ndarray: ...
def pts_to_midstep(x: np.ndarray, *args: np.ndarray) -> np.ndarray: ...

STEP_LOOKUP_MAP: dict[str, Callable]

def index_of(y: float | ArrayLike) -> tuple[np.ndarray, np.ndarray]: ...
def safe_first_element(obj: Collection[_T]) -> _T: ...
def sanitize_sequence(data): ...
def normalize_kwargs(
    kw: dict[str, Any],
    alias_mapping: dict[str, list[str]] | type[Artist] | Artist | None = ...,
) -> dict[str, Any]: ...

class _OrderedSet(collections.abc.MutableSet):
    def __init__(self) -> None: ...
    def __contains__(self, key) -> bool: ...
    def __iter__(self): ...
    def __len__(self) -> int: ...
    def add(self, key) -> None: ...
    def discard(self, key) -> None: ...

def _format_approx(number: float, precision: int) -> str: ...
