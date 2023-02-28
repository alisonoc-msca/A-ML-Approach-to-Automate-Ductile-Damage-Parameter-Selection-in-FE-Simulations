import warnings
from B_SCR.Parameter_Space import ParameterSpace
from B_SCR.Acquisition_utilies import locate_max, random_num_gen
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.gaussian_process import GaussianProcessRegressor

class BayesianOptimization():
    """A function to identify the optimal combination of inputs to achieve
    a desired termination condition. """


    def __init__(self, f, pbounds, random_state=None, verbose=2,
                 bounds_transformer=None):
        self._random_state = random_num_gen(random_state)
        self._space = ParameterSpace(f, pbounds, random_state)
        self._gp = GaussianProcessRegressor(kernel=Matern(nu=1)*ConstantKernel()+WhiteKernel(),
                                            alpha=1e-6,
                                            normalize_y=True,
                                            n_restarts_optimizer=5,
                                            random_state=self._random_state)
        self._verbose = verbose
        self._bounds_transformer = bounds_transformer
        if self._bounds_transformer:
            try:
                self._bounds_transformer.initialize(self._space)
            except (AttributeError, TypeError):
                raise TypeError('The transformer must be an instance of DomainTransformer')
        super(BayesianOptimization, self).__init__()

    @property
    def gp(self):
        return self._gp
    @property
    def space(self):
        return self._space

    @property
    def max(self):
        return self._space.max()

    @property
    def min(self):
        return self._space.min()

    @property
    def res(self):
        return self._space.res()
    @property
    def bounds(self):
        return self._space.bounds

    def Contains(self,X):
        return self._space.Contains(X)

    def register(self, params, target):
        self._space.register(params, target)

    def suggest(self, utility_function):
        if len(self._space) == 0:
            return self._space.array_to_params(self._space.random_sample())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._gp.fit(self._space.params, self._space.target)
        suggestion = locate_max(acq_fn=utility_function.utility_func,
                                gp_model=self._gp,
                                current_max=self._space.target.max(),
                                parameter_bounds=self._space.bounds,
                                random_state=self._random_state)
        if self._bounds_transformer:
                self.set_bounds(self._bounds_transformer.transform(self._space))
        return self._space.array_to_params(suggestion)

    def set_bounds(self, new_bounds):
        self._space.set_bounds(new_bounds)
