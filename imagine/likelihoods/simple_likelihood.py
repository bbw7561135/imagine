import numpy as np
from copy import deepcopy

from imagine.observables.observable import Observable
from imagine.observables.observable_dict import Measurements, Simulations, Covariances
from imagine.likelihoods.likelihood import Likelihood

class SimpleLikelihood(Likelihood):

    '''
    measurement_dict
        -- Measurements object
    covariance_dict
        -- Covariances object
    observable_dict (in __call__)
        -- Simulations object
    '''
    def __init__(self, measurement_dict, covariance_dict=None):
        self.measurement_dict = measurement_dict
        self.covariance_dict = covariance_dict

    @property
    def measurement_dict(self):
        return self._measurement_dict

    @measurement_dict.setter
    def measurement_dict(self, measurement_dict):
        assert isinstance(measurement_dict, Measurements)
        self._measurement_dict = measurement_dict

    @property
    def covariance_dict(self):
        return self._covariance_dict

    @covariance_dict.setter
    def covariance_dict(self, covariance_dict):
        if covariance_dict is not None:
            assert isinstance(covariance_dict, Covariances)
        self._covariance_dict = covariance_dict
    
    # notice the argument should be a dict of Observable objects
    def __call__(self, observable_dict):
        # check dict entries
        assert (observable_dict.keys() == self._measurement_dict.keys())
        likelicache = float(0)
        if self._covariance_dict is None:
            for name in self._measurement_dict.keys():
                obs_mean = deepcopy(observable_dict[name].ensemble_mean)
                data = deepcopy(self._measurement_dict[name].to_global_data())
                diff = np.nan_to_num(data - obs_mean)
                likelicache += -float(0.5)*float(np.vdot(diff,diff))
        else:
            assert (observable_dict.keys() == self._covariance_dict.keys())
            for name in self._measurement_dict.keys():
                obs_mean = deepcopy(observable_dict[name].ensemble_mean)
                data = deepcopy(self._measurement_dict[name].to_global_data())
                cov = deepcopy(self._covariance_dict[name].to_global_data())
                diff = np.nan_to_num(data - obs_mean)
                (sign,logdet) = np.linalg.slogdet(cov*2.*np.pi)
                likelicache += -float(0.5)*float(np.vdot(diff,np.linalg.solve(cov,diff.T))+sign*logdet)
        return likelicache
