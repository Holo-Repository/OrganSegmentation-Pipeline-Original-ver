"""
This module contains marching cube functionality.
"""

import logging
from typing import Tuple

import numpy as np
from skimage import measure


def generate_mesh(
    image_data: np.ndarray, threshold=300, step_size=1
) -> Tuple[np.array, np.array, np.array]:
    logging.info("Generating mesh")
    logging.info("Marching cubes: Transposing surface")

    # For NIfTI with 5D shape (time etc.); most NIfTI comes in 3D anyway
    if len(image_data.shape) == 5:
        image_data = image_data[:, :, :, 0, 0]
    volume = image_data.transpose((2, 1, 0))

    logging.info("Marching cubes: Calculating surface...")
    verts, faces, norm, val = measure.marching_cubes_lewiner(
        volume, threshold, step_size=step_size, allow_degenerate=True
    )

    aligned_verts = align_mesh_with_pivot(verts, [0.0, 0.0, 0.0]) 

    return aligned_verts, faces, norm

def seperate_segmentation(data: np.ndarray, unique_values: list = []) -> np.ndarray:
        """
        Seperate unique values into a new dimension. If no unique values are
        given, np.unique() will be used.
        """
        if not unique_values:
            unique_values = np.unique(data)
        result = np.zeros((len(unique_values),) + data.shape)
        for i, value in enumerate(unique_values):
            temp = np.array(data)
            temp[temp != value] = 0
            result[i] = temp
        return result

def align_mesh_with_pivot(verts: np.ndarray, pivot: Tuple[float, float, float]) -> np.ndarray:
    center = np.mean(verts, axis=0)  # Calculate the center of the mesh
    offset = np.array(pivot) - center  # Calculate the offset between the pivot and the center
    aligned_verts = verts + offset  # Translate the vertices by the offset
    return aligned_verts
