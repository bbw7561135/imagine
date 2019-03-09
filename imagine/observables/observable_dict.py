"""
for convenience we define dictionary of Observable objects as
ObservableDict and inherit from which,
we define Measurements, Covariances, Simulations and Masks
for storing
    -- observational data sets
    -- observational covariances
    -- simulated ensemble sets
    -- HEALPix mask maps
separately

by HEALPix convention,
masked erea associated with pixel value 0,
unmasked area with pixel value 1

notice covariance matrix should not have Observable structure,
instead, it can be a single domain NIFTy5 Field or numpy ndarray,
nevertheless, we make ObservableDict flexible enough

observable name/unit convention:
* ('fd','nan',str(size/Nside),'nan')
    -- Faraday depth (in unit
* ('dm','nan',str(pix),'nan')
    -- dispersion measure (in unit
* ('sync',str(freq),str(pix),X)
    -- synchrotron emission
    X stands for:
    * 'I'
        -- total intensity (in unit K-cmb)
    * 'Q'
        -- Stokes Q (in unit K-cmb, IAU convention)
    * 'U'
        -- Stokes U (in unit K-cmb, IAU convention)
    * 'PI'
        -- polarisation intensity (in unit K-cmb)
    * 'PA'
        -- polarisation angle (in unit rad, IAU convention)

remarks on observable name:
    -- str(freq), polarisation-related-flag are redundant for Faraday depth and dispersion measure
    so we put 'nan' instead
    -- str(pix/nside) stores either Healpix Nisde, or just number of pixels/points
    we do this for flexibility, in case users have non-HEALPix based in/output

mask method:
    -- mask only applies to observables/covariances
    observable after masking will be re-recorded as plain data type
"""

import numpy as np
import logging as log

from nifty5 import Field, RGSpace, HPSpace, DomainTuple

from imagine.observables.observable import Observable
from imagine.tools.masker import mask_obs, mask_cov
from imagine.tools.icy_decorator import icy


@icy
class ObservableDict(object):
    """
    add/update name and data with function .append
    """
    def __init__(self):
        self._archive = dict()

    @property
    def archive(self):
        return self._archive

    def keys(self):
        return self._archive.keys()
    
    def __getitem__(self, key):
        return self._archive[key]

    def append(self, name, data, plain=False):
        """

        :param name: str tuple
        notice: name should follow convention
        (data-name,str(data-freq),str(data-Nside/size),str(pol))
        if data is independent from frequency, set 'nan'
        pol should be either 'I','Q','U','PI','PA' or 'nan'

        :param data: ndarray/Field/Observable
        we require 1d ndarray not in 'vector' shape (n,) but (1,n)

        :param plain: if True, means unstructured data
        if False(default), means healpix structured sky map

        :return:
        """
        pass

    def apply_mask(self, mask_dict):
        """
        apply mask maps
        :param mask_dict: Masks object
        """
        pass


@icy
class Masks(ObservableDict):

    def __init__(self):
        super(Masks, self).__init__()

    def append(self, name, data, plain=False):
        assert (len(name) == 4)
        if isinstance(data, Observable):
            assert (data.domain.shape[0] == 1)
            raw_data = data.to_global_data()
            for i in raw_data[0]:
                assert (i == float(0) or i == float(1))
            self._archive[name] = data
        elif isinstance(data, Field):
            assert (data.domain.shape[0] == 1)
            raw_data = data.to_global_data()
            for i in raw_data[0]:
                assert (i == float(0) or i == float(1))
            self._archive[name] = Observable(data.domain, data.to_global_data())
        elif isinstance(data, np.ndarray):
            assert (data.shape[0] == 1)
            for i in data[0]:
                assert (i == float(0) or i == float(1))
            if plain:
                assert (data.shape[1] == int(name[2]))
                domain = DomainTuple.make((RGSpace(int(1)), RGSpace(data.shape[1])))
            else:
                assert (data.shape[1] == 12*int(name[2])*int(name[2]))              
                domain = DomainTuple.make((RGSpace(int(1)), HPSpace(nside=int(name[2]))))
            self._archive[name] = Observable(domain, data)
        else:
            raise TypeError('unsupported data type')
        log.debug('mask-dict appends data %s' % str(name))


@icy
class Measurements(ObservableDict):

    def __init__(self):
        super(Measurements, self).__init__()

    def append(self, name, data, plain=False):
        assert (len(name) == 4)
        if isinstance(data, Observable):
            assert (data.domain.shape[0] == 1)
            self._archive[name] = data  # rw
        elif isinstance(data, Field):
            assert (data.domain.shape[0] == 1)
            self._archive[name] = Observable(data.domain, data.to_global_data())  # rw
        elif isinstance(data, np.ndarray):
            assert (data.shape[0] == 1)
            if plain:
                assert (data.shape[1] == int(name[2]))
                domain = DomainTuple.make((RGSpace(int(1)), RGSpace(data.shape[1])))
            else:
                assert (data.shape[1] == 12*int(name[2])*int(name[2]))
                domain = DomainTuple.make((RGSpace(int(1)), HPSpace(nside=int(name[2]))))
            self._archive[name] = Observable(domain, data)  # rw
        else:
            raise TypeError('unsupported data type')
        log.debug('measurements-dict appends data %s' % str(name))

    def apply_mask(self, mask_dict):
        if mask_dict is None:
            pass
        else:
            assert isinstance(mask_dict, Masks)
            for name, msk in mask_dict._archive.items():
                masked = mask_obs(self._archive[name].to_global_data(), msk.to_global_data())
                new_name = (name[0], name[1], str(masked.shape[1]), name[3])
                self._archive.pop(name, None)  # pop out obsolete
                self.append(new_name, masked, plain=True)  # append new as plain data


@icy
class Simulations(ObservableDict):

    def __init__(self):
        super(Simulations, self).__init__()

    def append(self, name, data, plain=False):
        """
        mind its difference from Measurements
        :param name:
        :param data:
        :param plain:
        :return:
        """
        assert (len(name) == 4)
        if name in self._archive.keys():  # app
            self._archive[name].append(data)
        else:  # new
            if isinstance(data, Observable):
                self._archive[name] = data
            elif isinstance(data, Field):
                self._archive[name] = Observable(data.domain, data.to_global_data())
            elif isinstance(data, np.ndarray):
                if plain:
                    assert (data.shape[1] == int(name[2]))
                    domain = DomainTuple.make((RGSpace(data.shape[0]), RGSpace(data.shape[1])))
                else:
                    assert (data.shape[1] == 12*int(name[2])*int(name[2]))
                    domain = DomainTuple.make((RGSpace(data.shape[0]), HPSpace(nside=int(name[2]))))
                self._archive[name] = Observable(domain, data)
            else:
                raise TypeError('unsupported data type')
        log.debug('observable-dict appends data %s' % str(name))

    def apply_mask(self, mask_dict):
        if mask_dict is None:
            pass
        else:
            assert isinstance(mask_dict, Masks)
            for name, msk in mask_dict._archive.items():
                masked = mask_obs(self._archive[name].to_global_data(), msk.to_global_data())
                new_name = (name[0], name[1], str(masked.shape[1]), name[3])
                self._archive.pop(name, None)  # pop out obsolete
                self.append(new_name, masked, plain=True)  # append new as plain data


@icy
class Covariances(ObservableDict):

    def __init__(self):
        super(Covariances, self).__init__()

    def append(self, name, data, plain=False):
        """
        matrix coming in, numpy.matrix is not recommended
        :param name:
        :param data:
        :param plain:
        :return:
        """
        assert (len(name) == 4)
        assert (data.shape[0] == data.shape[1])
        if plain:
            assert (data.shape[0] == int(name[2]))
        else:
            assert (data.shape[0] == 12*int(name[2])*int(name[2]))
        if isinstance(data, Field):
            assert (len(data.domain) == 1)  # single domain
            self._archive[name] = data  # rw
        elif isinstance(data, np.ndarray):
            domain = DomainTuple.make(RGSpace(shape=data.shape))
            self._archive[name] = Field.from_global_data(domain, data)  # rw
        else:
            raise TypeError('unsupported data type')
        log.debug('covariances-dict appends data %s' % str(name))

    def apply_mask(self, mask_dict):
        if mask_dict is None:
            pass
        else:
            assert isinstance(mask_dict, Masks)
            for name, msk in mask_dict._archive.items():
                masked = mask_cov(self._archive[name].to_global_data(), msk.to_global_data())
                new_name = (name[0], name[1], str(masked.shape[1]), name[3])
                self._archive.pop(name, None)  # pop out obsolete
                self.append(new_name, masked, plain=True)  # append new as plain data
