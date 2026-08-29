"""Neigbors data management class"""

import numpy as np


class NeighborsData:
    def __init__(self, entities):

        self.entities = entities

        self.nb_mask = None
        self.sources = None
        self.targets = None
        self.candidates_sources = None
        self.candidates_targets = None
        self.offsets = None
        self.distance_squared = None
        self.nb_count = None

    def rebuild(self, candidates_sources, candidates_targets):

        self.candidates_sources = candidates_sources
        self.candidates_targets = candidates_targets

        offsets = (
            self.entities.positions[self.candidates_sources]
            - self.entities.positions[self.candidates_targets]
        )
        distance_squared = np.sum(offsets**2, axis=1)
        valid = distance_squared < self.entities.sensor_range_squared

        self.sources = self.candidates_sources[valid]
        self.targets = self.candidates_targets[valid]

        self.offsets = offsets[valid]
        self.distance_squared = distance_squared[valid]

        self.nb_count = np.bincount(
            self.sources,
            minlength=self.entities.count,
        )
