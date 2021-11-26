from typing import List

import healpy as hp
import numpy as np

from zodipy._components import Component
from zodipy._integration import line_of_sight_integrate


def instantaneous_emission(
    nside: int,
    freq: float,
    components: List[Component],
    emissivities: List[float],
    line_of_sights: List[np.ndarray],
    observer_positions: np.ndarray,
    earth_positions: np.ndarray,
    coord_out: str,
) -> np.ndarray:
    """Returns the simulated instantaneous emission.

    The emission is that seen by an observer at an instant at a single time
    or as the average of multiple times if several observer and Earth
    coordinates are provided.

    Parameters:
    -----------
    nside
        HEALPIX map resolution parameter.
    freq:
        Frequency of the observer in GHz.
    components:
        Dictionary containing the Zodiacal Component that is used to evaluate
        the emission.
    emissivities:
        Sequency of emissivities, one for each component, corresponding to the
        frequency of `freq`.
    observer_positions
        A sequence of (or a single) heliocentric positions of the observer.
    earth_positions
        A sequence of (or a single) heliocentric positions of the Earth.
    coord_out
        Coordinate frame of the output map.
    """

    npix = hp.nside2npix(nside)
    unit_vectors = _get_unit_vectors(
        nside=nside,
        pixels=np.arange(npix),
        coord_out=coord_out,
    )
    emission = np.zeros((len(components), npix))

    for observer_position, earth_position in zip(
        observer_positions,
        earth_positions,
    ):
        for idx, component in enumerate(components):
            integrated_comp_emission = line_of_sight_integrate(
                line_of_sight=line_of_sights[idx],
                get_emission_func=component.get_emission,
                observer_position=observer_position,
                earth_position=earth_position,
                unit_vectors=unit_vectors,
                freq=freq,
            )

            emission[idx] += integrated_comp_emission * emissivities[idx]

    return emission * 1e20


def time_ordered_emission(
    nside: int,
    freq: float,
    components: List[Component],
    emissivities: List[float],
    line_of_sights: List[np.ndarray],
    observer_position: np.ndarray,
    earth_position: np.ndarray,
    pixel_chunk: np.ndarray,
    bin: bool,
    coord_out: str,
) -> np.ndarray:
    """Simulates and returns the Zodiacal emission timestream.

    Parameters:
    -----------
    nside
        HEALPIX map resolution parameter.
    freq:
        Frequency of the observer in GHz.
    components:
        Dictionary containing the Zodiacal Component that is used to evaluate
        the emission.
    emissivities:
        Sequency of emissivities, one for each component, corresponding to the
        frequency of `freq`.
    observer_position
        Heliocentric position of the observer.
    earth_position
        Heliocentric position of the Earth.
    bin
        If True, return a binned HEALPIX map of the emission. If False, the
        timestream is returned.
    coord_out
        Coordinate frame of the output map.

    Returns
    -------
        Zodiacal emission [MJy/sr] over a timestream of pixels, or the
        binned Zodiacal emission map if bin is set to True.
    """

    if bin:
        pixels, counts = np.unique(pixel_chunk, return_counts=True)
        unit_vectors = _get_unit_vectors(
            nside=nside,
            pixels=pixels,
            coord_out=coord_out,
        )
        emission = np.zeros((len(components), hp.nside2npix(nside)))

        for idx, component in enumerate(components):
            integrated_comp_emission = line_of_sight_integrate(
                line_of_sight=line_of_sights[idx],
                get_emission_func=component.get_emission,
                observer_position=observer_position,
                earth_position=earth_position,
                unit_vectors=unit_vectors,
                freq=freq,
            )
            emission[idx, pixels] = integrated_comp_emission * emissivities[idx]

        emission[:, pixels] *= counts

        return emission * 1e20

    pixels, indicies = np.unique(pixel_chunk, return_inverse=True)
    unit_vectors = _get_unit_vectors(
        nside=nside,
        pixels=pixels,
        coord_out=coord_out,
    )
    time_stream = np.zeros((len(components), len(pixel_chunk)))

    for idx, component in enumerate(components):
        integrated_comp_emission = line_of_sight_integrate(
            line_of_sight=line_of_sights[idx],
            get_emission_func=component.get_emission,
            observer_position=observer_position,
            earth_position=earth_position,
            unit_vectors=unit_vectors,
            freq=freq,
        )

        time_stream[idx] = integrated_comp_emission[indicies] * emissivities[idx]

    return time_stream * 1e20


def _get_unit_vectors(nside: int, pixels: np.ndarray, coord_out: str) -> np.ndarray:
    """Returns the unit vectors on a HEALPIX map given a requested coordinate system.

    If the requested output system is not ecliptic ("E"), we need to rotate the
    vectors to ecliptic before evaluating the model.
    """

    unit_vectors = np.asarray(hp.pix2vec(nside, pixels))
    if coord_out != "E":
        r = hp.rotator.Rotator(coord=[coord_out, "E"])
        unit_vectors = r(unit_vectors)

    return np.asarray(unit_vectors)