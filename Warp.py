import numpy as np

class PosWarp:

    def __init__(self, pos_f):
        if pos_f(0) != 0:
            raise ValueError("Function must pass through (0,0)")
        self.pos_f = pos_f
    
    def sample(self, num_splits):
        indices = np.linspace(0, 1, num_splits)
        unnorm_pos = [self.pos_f(i) for i in indices]
        return np.array([p/unnorm_pos[-1] for p in unnorm_pos])
    
class RelWarp:

    def __init__(self, rel_f):
        self.rel_f = rel_f
    
    def sample(self, num_splits):
        indices = np.linspace(0, 1, num_splits)
        res = [0]
        for i in indices[1:]:
            res.append(res[-1] + self.rel_f(i))
        return np.array([r/res[-1] for r in res])
