from matplotlib.tri._triangulation import Triangulation
from matplotlib.tri._triinterpolate import TriInterpolator

import numpy as np
from numpy.typing import ArrayLike

class TriRefiner:
    def __init__(self, triangulation: Triangulation) -> None: ...

class UniformTriRefiner(TriRefiner):
    def __init__(self, triangulation: Triangulation) -> None: ...
    def refine_triangulation(
        self, return_tri_index: bool = ..., subdiv: int = ...
    ) -> tuple[Triangulation, np.ndarray]: ...
    def refine_field(
        self,
        z: ArrayLike,
        triinterpolator: TriInterpolator | None = ...,
        subdiv: int = ...,
    ) -> tuple[Triangulation, np.ndarray]: ...
