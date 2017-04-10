from __future__ import division
from __future__ import absolute_import
import numpy as np
from .vector import Vector, vector_map


class Matrix(object):
    def __init__(self, m, n, data=None):
        self.m = m
        self.n = n
        self.matrix = [Vector(n) for i in range(m)]

        if data is not None:
            for i in range(self.m):
                for j in range(self.n):
                    self.set_value(i, j, data[i][j])

    def set_value(self, m, n, v):
        self.matrix[m].set_value(n, v)

    def set_column(self, n, column):
        for i in range(column.__len__()):
            self.set_value(i, n, column[i])

    def set_row(self, m, row):
        for j in range(row.__len__()):
            self.set_value(m, j, row[j])

    def get_value(self, m, n):
        return self.matrix[m].get_value(n)

    def get_row(self, m):
        return self.matrix[m]

    def get_column(self, n):
        column = Vector(self.m)

        for i in range(self.m):
            column.set_value(i, self.matrix[i].get_value(n))

        return column

    def get_column_space(self):
        return [self.get_column(j) for j in range(self.n)]

    def get_row_space(self):
        return self.matrix

    def get_real(self):
        C = Matrix(self.m, self.n)

        j = 0
        for row in map(vector_map, self.get_row_space()):
            C.set_row(j, list(map(lambda x: x.real, row)))

        return C

    def get_imag(self):
        C = Matrix(self.m, self.n)

        j = 0
        for row in map(vector_map, self.get_row_space()):
            C.set_row(j, list(map(lambda x: x.imag, row)))

        return C

    def get_mse(self, B):
        C = Matrix(self.m, self.n)

        j = 0
        for a in map(lambda x: np.array(x.vector), self.get_column_space()):
            b = np.array(B.get_column(j).vector)

            C.set_column(j, np.square(b - a) / self.m)

            j += 1

        return C

    def __str__(self):
        res = []

        for i in range(self.m):
            arr = []
            res.append(arr)
            for j in range(self.n):
                arr.append(str(self.get_value(i, j)))

        return "\n".join((list(map(lambda x: "\t".join(x), res))))