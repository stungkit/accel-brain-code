# -*- coding: utf-8 -*-
from accelbrainbase.iteratable_data import IteratableData
from accelbrainbase.samplabledata.pretext_sampler import PretextSampler
from abc import abstractmethod


class SSDATransformerIterator(IteratableData):
    '''
    Iterator for the Self-supervised Domain Adaptive Transformer.
    '''

    # `list` of `PretextSampler`s.
    __pretext_samplers_list = []

    def get_pretext_samplers_list(self):
        ''' getter for `list` of `PretextSampler`s. '''
        if isinstance(self.__pretext_samplers_list, list) is False:
            raise TypeError("The type of this property must be `list`.")
        if len(self.__pretext_samplers_list) == 0:
            raise ValueError("Number of elements in this property must be more than zero.")

        for i in range(len(self.__pretext_samplers_list)):
            if isinstance(self.__pretext_samplers_list[i], PretextSampler) is False:
                raise TypeError("The type of value of this property must be `PretextSampler`.")
        return self.__pretext_samplers_list

    def set_pretext_samplers_list(self, value):
        ''' setter for `list` of `PretextSampler`s. '''
        if isinstance(value, list) is False:
            raise TypeError("The type of this property must be `list`.")
        for i in range(len(value)):
            if isinstance(value[i], PretextSampler) is False:
                raise TypeError("The type of value of this property must be `PretextSampler`.")

        self.__pretext_samplers_list = value

    pretext_samplers_list = property(get_pretext_samplers_list, set_pretext_samplers_list)

    @abstractmethod
    def generate_learned_samples(self):
        '''
        Draw and generate learned samples.

        Returns:
            `Tuple` data. The shape is ...
            - encoder's observed data points in training.
            - decoder's observed data points in training.
            - encoder's masked data points in training.
            - decoder's masked data points in training.
            - encoder's observed data points in test.
            - decoder's observed data points in test.
            - encoder's masked data points in test.
            - decoder's masked data points in test.
            - Labeled data for downstream task in training.
            - Labeled data for downstream task in test.
            - `list` of encoder's observed data points in pretext task.
            - `list` of decoder's observed data points in pretext task.
            - `list` of encoder's masked data points in pretext task.
            - `list` of decoder's masked data points in pretext task.
            - `list` of labeled data in pretext task.
        '''
        raise NotImplementedError()

    def create_pretext_task_samples_list(self, target_domain_batch_arr):
        '''
        Create samples for pretext_task.

        Args:
            target_domain_batch_arr:    `nd.ndarray` of samples in target domain.
        
        Returns:
            Tuple data. The shape is ...
            - `list` of pretext task samples.
            - `list` of pretext task labels. The order of the elements corresponds to the pretext task samples.
        '''
        pretext_encoded_observed_arr_list = []
        pretext_decoded_observed_arr_list = []
        pretext_encoded_mask_arr_list = []
        pretext_decoded_mask_arr_list = []
        pretext_label_arr_list = []
        
        for i in range(len(self.pretext_samplers_list)):
            self.pretext_samplers_list[i].preprocess(target_domain_batch_arr)
            arr_tuple = self.pretext_samplers_list[i].draw()
            (
                pretext_encoded_observed_arr, 
                pretext_decoded_observed_arr, 
                pretext_encoded_mask_arr, 
                pretext_decoded_mask_arr, 
                pretext_label_arr
            ) = arr_tuple
            pretext_encoded_observed_arr_list.append(
                pretext_encoded_observed_arr
            )
            pretext_decoded_observed_arr_list.append(
                pretext_decoded_observed_arr
            )
            pretext_encoded_mask_arr_list.append(
                pretext_encoded_mask_arr
            )
            pretext_decoded_mask_arr_list.append(
                pretext_decoded_mask_arr
            )
            pretext_label_arr_list.append(
                pretext_label_arr
            )

        return (
            pretext_encoded_observed_arr_list,
            pretext_decoded_observed_arr_list,
            pretext_encoded_mask_arr_list,
            pretext_decoded_mask_arr_list,
            pretext_label_arr_list
        )

    def pre_normalize(self, arr):
        '''
        Normalize before observation.

        Args:
            arr:    Tensor.
        
        Returns:
            Tensor.
        '''
        if self.__norm_mode == "min_max":
            if arr.max() != arr.min():
                n = 0.0
            else:
                n = 1e-08
            arr = (arr - arr.min()) / (arr.max() - arr.min() + n)
        elif self.__norm_mode == "z_score":
            std = arr.asnumpy().std()
            if std == 0:
                std += 1e-08
            arr = (arr - arr.mean()) / std

        arr = arr * self.__scale
        return arr

    def set_readonly(self, value):
        ''' setter '''
        raise TypeError("This property must be read-only.")

    def get_epochs(self):
        ''' getter '''
        return self.__epochs

    def set_epochs(self, value):
        ''' setter '''
        self.__epochs = value

    epochs = property(get_epochs, set_epochs)

    def get_batch_size(self):
        ''' getter '''
        return self.__batch_size

    def set_batch_size(self, value):
        ''' setter '''
        self.__batch_size = value

    batch_size = property(get_batch_size, set_batch_size)

    __norm_mode = "z_score"

    def get_norm_mode(self):
        ''' getter '''
        return self.__norm_mode
    
    def set_norm_mode(self, value):
        ''' setter '''
        self.__norm_mode = value
    
    norm_mode = property(get_norm_mode, set_norm_mode)

    __scale = 1.0

    def get_scale(self):
        ''' getter '''
        return self.__scale
    
    def set_scale(self, value):
        ''' setter '''
        self.__scale = value
    
    scale = property(get_scale, set_scale)
