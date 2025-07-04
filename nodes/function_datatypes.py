from abc import ABC, abstractmethod

import numpy as np
import sympy as sp

from nodes.prop_types import PT_Function
from nodes.prop_values import PropValue


class Function(PropValue, ABC):
    @abstractmethod
    def get(self):
        pass

    @property
    def type(self):
        return PT_Function()


class IdentityFun(Function):
    def get(self):
        return lambda x: x


class CubicFun(Function):
    def __init__(self, a, b, c, d):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

    def get(self):
        return lambda x: self.a * (x ** 3) + self.b * (x ** 2) + self.c * x + self.d


class CustomFun(Function):
    def __init__(self, symbols, parsed_expr):
        self.symbols = symbols
        self.parsed_expr = parsed_expr

    def get(self):
        try:
            f = sp.lambdify(self.symbols, self.parsed_expr)
        except:
            f = lambda x: x
        return f


class PiecewiseFun(Function):
    def __init__(self, xs, ys):
        self.xs = xs
        self.ys = ys

    def get(self):
        return lambda i: np.interp(i, self.xs, self.ys)
