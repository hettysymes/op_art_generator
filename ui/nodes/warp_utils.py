import numpy as np

def validate(f):
    if f(0) != 0:
        raise ValueError("Function must pass through (0,0).")
    elif f(1) == 0:
        raise ValueError("Function cannot pass through (1,0).")

def normalise(l: np.ndarray):
    return l / l[-1]

def sample_fun(f, num_samples):
    indices = np.linspace(0, 1, num_samples)
    return np.array([f(i) for i in indices])

class PosWarp:

    def __init__(self, pos_f):
        validate(pos_f)
        self.pos_f = pos_f

    def sample(self, num_samples):
        unnorm_pos = sample_fun(self.pos_f, num_samples)
        return normalise(unnorm_pos)


class RelWarp:

    def __init__(self, rel_f):
        validate(rel_f)
        self.rel_f = rel_f

    def sample(self, num_samples):
        indices = np.linspace(0, 1, num_samples)
        unnorm_pos = np.zeros(num_samples)
        for i in range(1, num_samples):
            unnorm_pos[i] = unnorm_pos[i - 1] + self.rel_f(indices[i])
        return normalise(unnorm_pos)
