from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from zodipy.models import model_registry
from zodipy._model import Model
from zodipy._labels import CompLabel

DEFAULT_EARTH_POS = np.array([1.0, 0.0, 0.0])


def tabulate_density(
    grid: NDArray[np.floating] | list[NDArray[np.floating]],
    model: str | Model = "DIRBE",
    earth_coords: NDArray[np.floating] = DEFAULT_EARTH_POS,
) -> NDArray[np.floating]:
    """Tabulates the component densities for a meshgrid."""

    if not isinstance(model, Model):
        model = model_registry.get_model(model)

    if not isinstance(grid, np.ndarray):
        grid = np.asarray(grid)

    model.comps[CompLabel.FEATURE].R = 1.2
    model.comps[CompLabel.FEATURE].sigma_r = 0.08

    X_0_cloud = model.comps[CompLabel.CLOUD].X_0
    X_0_cloud = np.reshape(X_0_cloud, (3, 1, 1, 1))
    earth_coords = np.reshape(earth_coords, (3, 1, 1, 1))

    density_grid = np.zeros((model.ncomps, *grid.shape[1:]))
    for idx, comp in enumerate(model.comps.values()):
        comp.X_0 = np.reshape(comp.X_0, (3, 1, 1, 1))
        density_grid[idx] = comp.compute_density(
            X_helio=grid,
            X_earth=earth_coords,
            X_0_cloud=X_0_cloud,
        )
        comp.X_0 = np.reshape(comp.X_0, (3, 1))

    return density_grid
