import numpy as np
from B_SCR.Acquisition_utilies import random_num_gen

def convert(x):
    """ returns tuple with floats of x values"""
    return tuple(map(float, x))

class ParameterSpace(object):
    """
    A CLASS TO STORE ALL THE DETAILS AND CONTROLS FOR TO THE PARAMETER SPACE
    """
    def __init__(self, target_func, pbounds, random_state=None):
        self.random_state = random_num_gen(random_state)
        self.target_func = target_func
        self._keys = sorted(pbounds)
        self._bounds = np.array([item[1] for item in sorted(pbounds.items(),
                                                            key=lambda x: x[0])],
                                dtype=np.float)
        self._params = np.empty(shape=(0, self.dim))
        self._target = np.empty(shape=(0))
        self._cache = {}

    def __contains__(self, x):
        return convert(x) in self._cache

    def __len__(self):
        assert len(self._params) == len(self._target)
        return len(self._target)

    @property
    def keys(self):
        return self._keys
    @property
    def params(self):
        return self._params
    @property
    def bounds(self):
        return self._bounds
    @property
    def target(self):
        return self._target
    @property
    def dim(self):
        return len(self._keys)
    def params_to_array(self, params):
        if isinstance(params, list):
            x = []
            for p in params:
                try:
                    assert set(p) == set(self.keys)
                except AssertionError:
                    raise ValueError(
                        "Parameters' keys ({}) do ".format(sorted(params)) + "not match the expected set of keys ({}).".format(self.keys))
                x.append(np.asarray([p[key] for key in self.keys]))
        else:
            try:
                assert set(params) == set(self.keys)
            except AssertionError:
                raise ValueError(
                    "Parameters' keys ({}) do ".format(sorted(params)) +"not match the expected set of keys ({}).".format(self.keys))
            x = np.asarray([params[key] for key in self.keys])
        return x

    def array_to_params(self, x):
        if isinstance(x, list):
            params = []
            for param in x:
                try:
                    assert len(param) == len(self.keys)
                except AssertionError:
                    raise ValueError(
                        "Size of array ({}) is different than the ".format(len(x)) +"expected number of parameters ({}).".format(len(self.keys)))
                params.append(dict(zip(self.keys, param)))
        else:
            try:
                assert len(x) == len(self.keys)
            except AssertionError:
                raise ValueError(
                    "Size of array ({}) is different than the ".format(len(x)) +"expected number of parameters ({}).".format(len(self.keys)))
            params = dict(zip(self.keys, x))
        return params

    def _as_array(self, x):
        try:
            x = np.asarray(x, dtype=float)
        except TypeError:
            x = self.params_to_array(x)
        x = x.ravel()
        try:
            assert x.size == self.dim
        except AssertionError:
            raise ValueError(
                "Size of array ({}) is different than the ".format(len(x)) +"expected number of parameters ({}).".format(len(self.keys)))
        return x

    def register(self, params, target):
        x = self._as_array(params)
        if x in self:
            pass
            # raise KeyError('Data point {} is not unique in continuous space'.format(x))
        self._cache[convert(x.ravel())] = target
        self._params = np.concatenate([self._params, x.reshape(1, -1)])
        self._target = np.concatenate([self._target, [target]])

    def set_bounds(self, new_bounds):
        for row, key in enumerate(self.keys):
            if key in new_bounds:
                self._bounds[row] = new_bounds[key]

    def max(self):
        try:
            res = {'target': self.target.max(), 'params': dict(zip(self.keys, self.params[self.target.argmax()]))}
        except ValueError:
            res = {}
        return res

    def min(self):
        try:
            res = {'target': self.target.min(), 'params': dict(zip(self.keys, self.params[self.target.argmin()]))}
        except ValueError:
            res = {}
        return res

    def res(self):
        params = [dict(zip(self.keys, p)) for p in self.params]
        return [{"target": target, "params": param} for target, param in zip(self.target, params)]

