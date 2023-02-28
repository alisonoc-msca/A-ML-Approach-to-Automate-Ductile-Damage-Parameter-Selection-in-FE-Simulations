from scipy.optimize import minimize
import numpy as np
from scipy.stats import norm


def random_num_gen(random_state=None):
	"""
    numpy function for generating random numbers where the size is variable
    """
	if random_state is None:
		random_state = np.random.RandomState()
	else:
		random_state = np.random.RandomState(random_state)
	return random_state


def locate_max(acq_fn, gp_model, current_max, parameter_bounds,
               random_state, n_random_samples=50000, n_optimisation_samples=100):
	"""Insert description about functions
	CHATGPT: LARGER NUMBER OF RANDOM SAMPLES FOR WARM UP PHASE WILL TYPICALY RESULT IN A BETTER STARTING POINT FOR THE OPTIMISATION PROCESS.
	THE NUMBER OF OPTIMISATION SAMPLES IS DIRECTLY PROPORTIONAL TO THE NUMBR OF FUNCTION EVALUATIONS. LARGER NUMBER MORE ACCURATE SOLUTION BUT ALSO LONGER COMPUTATION.
	"""
	# CREATE ARRAY N_RANDOM_SAMPLES X NUM_PARAMS
	warm_up = random_state.uniform(parameter_bounds[:, 0],
								   parameter_bounds[:, 1],
								   size=(n_random_samples, parameter_bounds.shape[0]))
	y_warm_up = acq_fn(warm_up, gp=gp_model, y_max=current_max)
	x_max = warm_up[y_warm_up.argmax()]
	max_acq = y_warm_up.max()
	# EXPLORE THE PARAMETER SPACE STRATEGICALLY
	x_points = random_state.uniform(parameter_bounds[:, 0],
									parameter_bounds[:, 1],
									size=(n_optimisation_samples, parameter_bounds.shape[0]))
	for intg, x in enumerate(x_points):
		# print('INTERGER %s/%s' %(intg, len(x_points)))
		temp_result = minimize(lambda i: acq_fn(i.reshape(1, -1),
												gp=gp_model,
												y_max=current_max),
							   x.reshape(1, -1),
							   bounds=parameter_bounds,
							   method="L-BFGS-B")
		# AFTER PASSING THE CURRENT MAX ABOVE TO THE MINIMISE FUNCTION,
		# SUCCESS CHECKS TO SEE IF TEMP_RESULT IS BETTER THAN THE CURRENT MAX
		if not temp_result.success:
			continue
		# STORE THE RESULT IF IT IS BETTER THAN THE PREVIOUS
		if max_acq is None or -temp_result.fun[0] >= max_acq:
			x_max = temp_result.x
			max_acq = -temp_result.fun[0]
	# NUMPY CLIP ENSURES THE NEW POINT IS WITHIN THE CURRENT BOUNDS
	return np.clip(x_max, parameter_bounds[:, 0], parameter_bounds[:, 1])


class AcquisitionUtilities(object):
	"""
    class that initialises the acquisition function to strategically sample the surrogate model
    """

	def __init__(self, aq_type, kappa, xi, step=10):
		self.kappa = kappa
		self.xi = xi
		self.step_size = step
		self._iterations = 0
		if aq_type not in ['EI', 'POI', 'UCB']:
			raise NotImplementedError(f"The acquisition function {format(aq_type)} is unavailable, "
									  f"please choose one of the available options EI, POI or UCB.")
		else:
			self.aq_type = aq_type

	def utility_func(self, x, gp, y_max):
		if self.aq_type == 'POI':
			return self._POI(x, gp, y_max, self.xi)
		if self.aq_type == 'UCB':
			return self._UCB(x, gp, self.kappa)
		if self.aq_type == 'EI':
			return self._EI(x, gp, y_max, self.xi)

	@staticmethod
	def _UCB(x, gp, kappa):
		mean, std = gp.predict(x, return_std=True)
		return mean + kappa * std

	@staticmethod
	def _EI(x, gp, y_max, xi):
		mean, std = gp.predict(x, return_std=True)
		a = (mean - y_max - xi)
		z = a / std
		return a * norm.cdf(z) + std * norm.pdf(z)

	@staticmethod
	def _POI(x, gp, y_max, xi):
		mean, std = gp.predict(x, return_std=True)
		z = (mean - y_max - xi) / std
		return norm.cdf(z)
