"""Spatial Grid management class"""

import numpy as np

from .config import config


class SpatialGrid:
    def __init__(self, cell_size):
        self.cell_size = cell_size

        # Grid's columns and rows are defined at start,
        # redimensionning the world at runtime would fail at this point
        self.cols = int(np.ceil(config.world.width / cell_size))
        self.rows = int(np.ceil(config.world.height / cell_size))

    def cell_index(self, position):
        x = int(position[0] // self.cell_size)
        y = int(position[1] // self.cell_size)

        return y * self.cols + x

    def rebuild(self, entities):
        cell_xy = (entities.positions // self.cell_size).astype(np.intp)
        cell_indices = cell_xy[:, 1] * self.cols + cell_xy[:, 0]

        self.sorted_boids = np.argsort(cell_indices, kind="quicksort")

        self.sorted_cells = cell_indices[self.sorted_boids]

        self.cell_counts = np.bincount(
            self.sorted_cells,
            minlength=self.cols * self.rows,
        )

        self.cell_starts = np.cumsum(self.cell_counts) - self.cell_counts

    def get_neighbor_cells(self, cell_index):
        x = cell_index % self.cols
        y = cell_index // self.cols

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nx = x + dx
                ny = y + dy

                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    yield ny * self.cols + nx

    def get_candidate_pairs(self):
        sources = []
        targets = []

        for ci in np.flatnonzero(self.cell_counts):
            start = self.cell_starts[ci]
            end = start + self.cell_counts[ci]
            cell = self.sorted_boids[start:end]

            # this cell's pairs
            if len(cell) > 1:
                i, j = np.triu_indices(len(cell), k=1)
                a = cell[i]
                b = cell[j]

                sources.append(np.concatenate([a, b]))
                targets.append(np.concatenate([b, a]))

            # neighbor cells pairs
            for ni in self.get_neighbor_cells(ci):
                if self.cell_counts[ni] == 0:
                    continue
                if ni <= ci:
                    continue

                start = self.cell_starts[ni]
                end = start + self.cell_counts[ni]
                neighbors = self.sorted_boids[start:end]

                if len(cell) == 0 or len(neighbors) == 0:
                    continue

                a, b = np.meshgrid(cell, neighbors, indexing="ij")

                a = a.ravel()
                b = b.ravel()

                sources.append(np.concatenate([a, b]))
                targets.append(np.concatenate([b, a]))

        return (
            np.concatenate(sources),
            np.concatenate(targets),
        )
