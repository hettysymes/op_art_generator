import numpy as np

class CatmullRomCurve:

    def __init__(self, points, s=0.5):
        self.geo_mat = np.array([[0, 1, 0, 0],
                                 [-s, 0, s, 0],
                                 [2*s, s-3, 3-2*s, -s],
                                 [-s, 2-s, s-2, s]])
        self.points = np.array(points)
        
        # Add two fake end points
        # First end point
        vec = 2*self.points[0] - self.points[1]
        self.points = np.vstack((vec, self.points))
        # Second end point
        vec = 2*self.points[-1] - self.points[-2]
        self.points = np.vstack((self.points, vec))

        self.num_splines = len(self.points) - 3
    
    def sample(self, u):
        if u < 0 or u > self.num_splines:
            # u out of bounds error
            return -1
        t, spline_idx = np.modf(u)
        pt_vec = self.points[int(spline_idx) : int(spline_idx)+4]
        t_vec = np.array([1, t, t**2, t**3])
        return t_vec @ self.geo_mat @ pt_vec
    
    def regular_sample(self, num_samples=1000):
        step = self.num_splines/num_samples
        samples = []
        for i in range(num_samples):
            u = step*i
            samples.append(self.sample(u))
        return samples