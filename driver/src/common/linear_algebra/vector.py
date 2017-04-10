def vector_map(v):
    return v.vector


class Vector(object):
    def __init__(self, n):
        self.n = n
        self.vector = [0 for y in range(n)]

    def __str__(self):
        return self.vector.__str__()

    def set_value(self, n, v):
        self.vector[n] = v

    def get_value(self, n):
        return self.vector[n]