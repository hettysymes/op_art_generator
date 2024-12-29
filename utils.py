import numpy as np

class CubicBezierCurve:

    def __init__(self, points):
        self.splines = []
        for i in range(0, len(points)-3, 3):
            self.splines.append(CubicBezierSpline(points[i:i+4]))

    def cumulative_spline_dists(self):
        dists = [self.splines[0].approx_dist()]
        for i in range(1, len(self.splines)):
            dists.append(self.splines[i].approx_dist() + dists[-1])
        return dists

    def approx_dist(self):
        return self.cumulative_spline_dists()[-1]

    def dist_to_u_lookup(self, dist):
        spline_dists = self.cumulative_spline_dists()
        # Find which spline
        i = 0
        if dist > spline_dists[0]:
            for i in range(1, len(self.splines)):
                if spline_dists[i-1] <= dist and dist <= spline_dists[i]:
                    break
            dist -= spline_dists[i-1]
        return i + self.splines[i].dist_to_t_lookup(dist)
    
    def dist_sample(self, dist):
        u = self.dist_to_u_lookup(dist)
        return self.sample(u)
    
    def sample(self, u):
        t, spline_idx = np.modf(u)
        return self.splines[int(spline_idx)].sample(t)
    
    def reg_dist_sample(self, num_samples = 10):
        samples = []
        approx_dist = self.approx_dist()
        step = approx_dist/num_samples
        dist = 0
        for _ in range(num_samples):
            samples.append(self.dist_sample(dist))
            dist += step
        return samples

    def path_data(self):
        i = 0
        path_data = ""
        for i in range(len(self.splines)):
            path_data += self.splines[i].path_data()
        return path_data
    
class CubicBezierSpline:
    def __init__(self, points):
        if len(points) != 4:
            print("Spline error: wrong number of points")
        self.geo_mat = np.array([[1, 0, 0, 0],
                                 [-3, 3, 0, 0],
                                 [3, -6, 3, 0],
                                 [-1, 3, -3, 1]])
        self.points = np.array(points)
        self._dtable = None # Array: (t,dist) pairs

    def dist_table(self):
        if self._dtable == None:
            self._dtable = self.calc_dist_table()
        return self._dtable

    def approx_dist(self):
        return self.dist_table()[-1][1]

    def sample(self, t):
        t_vec = np.array([1, t, t**2, t**3])
        return t_vec @ self.geo_mat @ self.points

    def path_data(self):
        path_data = f"M {self.points[0][0]},{self.points[0][1]} C "
        for i in range(1, 4):
            path_data += f"{self.points[i][0]},{self.points[i][1]} "
        return path_data

    def reg_sample(self, num_samples = 1000):
        step = 1/num_samples
        samples = []
        for i in range(num_samples):
            t = step*i
            samples.append(self.sample(t))
        return samples
    
    def calc_dist_table(self, num_samples = 1000):
        dist_table = [(0,0) for _ in range(num_samples)]
        samples = self.reg_sample(num_samples=num_samples)
        step = 1/num_samples
        for i in range(1, num_samples):
            dist_table[i] = (step*i, dist_table[i-1][1] + np.linalg.norm(samples[i] - samples[i-1]))
        return dist_table

    def dist_to_t_lookup(self, dist):
        for i in range(1, len(self.dist_table())):
            t1, d1 = self.dist_table()[i-1]
            t2, d2 = self.dist_table()[i]
            if d1 <= dist and dist <= d2:
                break
        return t1 + ((dist - d1) / (d2 - d1))*(t2-t1)
    
    def dist_sample(self, dist):
        t = self.dist_to_t_lookup(dist)
        return self.sample(t)

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