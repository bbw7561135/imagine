'''
for convenience we define dictionary of Observable objects as
ObservableDict and inherit from which,
we define Measurements, Covariances and Simulations
for storing
    -- observational data sets
    -- observational covariances
    -- simulated ensemble sets
separately

notice covariance matrix should not have Observable structure,
instead, it can be a single domain NIFTy5 Field or numpy ndarray,
nevertheless, we make ObservableDict flexible enough
'''

import numpy as np
import logging as log

from nifty5 import Field, RGSpace, HPSpace, DomainTuple

from imagine.observables.observable import Observable

class ObservableDict(object):

    '''
    empty ctr, add/update name and data with function .append
    '''
    def __init__(self):
        self._archive = dict()

    @property
    def archive(self):
        return self._archive
    
    def __getitem__(self, key):
        return self._archive[key]

    '''
    name
        -- str tuple
        notice: name should follow convention
        (data-name,str(data-freq),str(data-Nside/size),str(pol))
        if data is independent from frequency, set 'nan'
        pol should be either 'I','Q','U','PI','PA' or 'nan'
    data
        -- list/tuple/ndarray/Field/Observable
    plain
        -- if True, means unstructured data
        if False(default), means healpix structured sky map
    '''
    def append(self,name,data,plain=False):
        pass

class Measurements(ObservableDict):

    def __init__(self):
        super(Measurements,self).__init__()

    def append(self,name,data,plain=False):
        assert (len(name) == 4)
        if isinstance(data, Observable):
            assert (data.domain.shape[0] == 1)
            self._archive[name] = data
        elif isinstance(data, (Field,Observable)):
            assert (data.domain.shape[0] == 1)
            self._archive[name] = Observable(data.domain,data.to_global_data())
        if isinstance(data, (list,tuple,np.ndarray)):
            if plain:
                assert (len(data) == int(name[2]))
                domain = DomainTuple.make((RGSpace(int(1)),RGSpace(len(data))))
            else:
                assert (len(data) == 12*int(name[2])*int(name[2]))
                domain = DomainTuple.make((RGSpace(int(1)),HPSpace(nside=int(name[2]))))
            self._archive[name] = Observable(domain,np.array(data))
        log.debug ('measurements-dict appends data %s' % str(name))
        
class Simulations(ObservableDict):

    def __init__(self):
        super(Simulations,self).__init__()

    # mind its difference from Measurements
    def append(self,name,data,plain=False):
        assert (len(name) == 4)
        if isinstance(data, Observable):
            self._archive[name] = data
        elif isinstance(data, (Field,Observable)):
            self._archive[name] = Observable(data.domain,data.to_global_data())
        elif isinstance(data, np.ndarray):
            if plain:
                assert (data.shape[1] == int(name[2]))
                domain = DomainTuple.make((RGSpace(data.shape[0]),RGSpace(data.shape[1])))
            else:
                assert (data.shape[1] == 12*int(name[2])*int(name[2]))
                domain = DomainTuple.make((RGSpace(data.shape[0]),HPSpace(nside=int(name[2]))))
            self._archive[name] = Observable(domain,data)
        log.debug ('simulations-dict appends data %s' % str(name))

class Covariances(ObservableDict):

    def __init__(self):
        super(Covariances,self).__init__()

    # matrix coming in, numpy.matrix is not recommended
    def append(self,name,data,plain=False):
        assert (len(name) == 4)
        assert (data.shape[0] == data.shape[1])
        if plain:
            assert (data.shape[0] == int(name[2]))
        else:
            assert (data.shape[0] == 12*int(name[2])*int(name[2]))
        if isinstance(data, Field):
            assert (len(data.domain) == 1) # single domain
            self._archive[name] = data
        elif isinstance(data, np.ndarray):
            domain = DomainTuple.make(RGSpace(shape=data.shape))
            self._archive[name] = Field.from_global_data(domain,data)
