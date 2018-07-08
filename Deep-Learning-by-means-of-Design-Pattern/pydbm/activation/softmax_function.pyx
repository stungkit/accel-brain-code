# -*- coding: utf-8 -*-
import numpy as np
cimport numpy as np
from pydbm.activation.interface.activating_function_interface import ActivatingFunctionInterface
ctypedef np.float64_t DOUBLE_t


class SoftmaxFunction(ActivatingFunctionInterface):
    '''
    Softmax function.
    '''

    def activate(self, np.ndarray x):
        '''
        Return the result from this activation function.

        Args:
            x   Parameter.

        Returns:
            The result.
        '''
        cdef np.ndarray exp_x
        cdef np.ndarray prob
        exp_x = np.exp(x - np.max(x))
        prob = exp_x / exp_x.sum(axis=0)
        return prob

    def derivative(self, np.ndarray x):
        '''
        Return of derivative with respect to this activation function.

        Args:
            x   Parameter.

        Returns:
            The result.
        '''
        cdef np.ndarray _x = x.reshape(-1,1)
        return np.diagflat(_x) - np.dot(_x, _x.T)
