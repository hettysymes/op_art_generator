from abc import ABC, abstractmethod

import numpy as np

from ui.nodes.function_datatypes import Function
from ui.nodes.prop_types import PT_Warp
from ui.nodes.prop_values import PropValue


class Warp(PropValue, ABC):
    @abstractmethod
    def sample(self, num_samples):
        pass

    @property
    def type(self):
        return PT_Warp()


def normalise(l: np.ndarray):
    if l[0] != 0:
        raise ValueError("Resulting function must pass through (0,0).")
    if l[-1] == 0:
        raise ValueError("Resulting function cannot pass through (1,0).")
    return l / l[-1]


def sample_fun(function: Function, num_samples):
    f = function.get()
    indices = np.linspace(0, 1, num_samples)
    return np.array([f(i) for i in indices])


class PosWarp(Warp):

    def __init__(self, pos_function):
        self.pos_function = pos_function
        self.sample(1000)  # Validation

    def sample(self, num_samples):
        unnorm_pos = sample_fun(self.pos_function, num_samples)
        return normalise(unnorm_pos)


class RelWarp(Warp):

    def __init__(self, rel_function):
        self.rel_function = rel_function
        self.sample(1000)  # Validation

    def sample(self, num_samples):
        rel_f = self.rel_function.get()
        indices = np.linspace(0, 1, num_samples)
        unnorm_pos = np.zeros(num_samples)
        for i in range(1, num_samples):
            unnorm_pos[i] = unnorm_pos[i - 1] + rel_f(indices[i])
        return normalise(unnorm_pos)
