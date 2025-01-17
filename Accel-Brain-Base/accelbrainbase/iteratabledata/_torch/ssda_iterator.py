# -*- coding: utf-8 -*-
from accelbrainbase.iteratabledata.ssda_iterator import SSDAIterator as _SSDAIterator
from accelbrainbase.extractabledata.image_extractor import ImageExtractor
from accelbrainbase.noiseable_data import NoiseableData

from abc import abstractmethod
import numpy as np
import torch

import pandas as pd
from logging import getLogger
import os


class SSDAIterator(_SSDAIterator):
    '''
    Iterator that draws from image files and generates `mxnet.ndarray`.

    References:
        - Ghifary, M., Kleijn, W. B., Zhang, M., Balduzzi, D., & Li, W. (2016, October). Deep reconstruction-classification networks for unsupervised domain adaptation. In European Conference on Computer Vision (pp. 597-613). Springer, Cham.
        - Xu, J., Xiao, L., & López, A. M. (2019). Self-supervised domain adaptation for computer vision tasks. IEEE Access, 7, 156694-156706., p156698.

    '''
    def __init__(
        self,
        image_extractor,
        dir_list,
        target_domain_dir_list,
        test_dir_list=None,
        epochs=300,
        batch_size=20,
        norm_mode="z_score",
        scale=1.0,
        noiseable_data=None,
        ctx="cpu"
    ):
        '''
        Init.

        Args:
            image_extractor:                is-a `ImageExtractor`.
            dir_list:                       `list` of directories that store your image files in training.
                                            This class will not scan the directories recursively and consider that
                                            all image file will be sorted by any rule in relation to your sequencial modeling.

            target_domain_dir_list:         `list` of directories that store your image files in DRCNetwork's domain adaptation.
                                            This class will not scan the directories recursively and consider that
                                            all image file will be sorted by any rule in relation to your sequencial modeling.

            test_dir_list:                  `list` of directories that store your image files in test.
                                            If `None`, this value will be equivalent to `dir_list`.
                                            This class will not scan the directories recursively and consider that
                                            all image file will be sorted by any rule in relation to your sequencial modeling.

            epochs:                         `int` of epochs of Mini-batch.
            batch_size:                     `int` of batch size of Mini-batch.
            norm_mode:                      How to normalize pixel values of images.
                                            - `z_score`: Z-Score normalization.
                                            - `min_max`: Min-max normalization.
                                            - others : This class will not normalize the data.

            scale:                          `float` of scaling factor for data.
            noiseable_data:                 is-a `NoiseableData` for Denoising Auto-Encoders.
            ctx:                            `mx.cpu()` or `mx.gpu()`.
        '''

        if isinstance(image_extractor, ImageExtractor) is False:
            raise TypeError("The type of `image_extractor` must be `ImageExtractor`.")
        if isinstance(dir_list, list) is False:
            raise TypeError("The type of `dir_list` must be `list`.")
        if noiseable_data is not None and isinstance(noiseable_data, NoiseableData) is False:
            raise TypeError("The type of `noiseable_data` must be `NoiseableData`.")

        logger = getLogger("accelbrainbase")
        self.__logger = logger

        dir_list.sort()
        self.__training_file_path_list = [None] * len(dir_list)
        dataset_size = 0
        for i in range(len(dir_list)):
            file_path_list = [dir_list[i] + "/" + file_name for file_name in os.listdir(dir_list[i] + "/")]
            file_path_list.sort()
            self.__training_file_path_list[i] = file_path_list
            dataset_size = dataset_size + len(file_path_list)

        iter_n = int(epochs * max(dataset_size / batch_size, 1))

        target_domain_dir_list.sort()
        self.__target_domain_file_path_list = [None] * len(target_domain_dir_list)
        for i in range(len(target_domain_dir_list)):
            file_path_list = [target_domain_dir_list[i] + "/" + file_name for file_name in os.listdir(target_domain_dir_list[i] + "/")]
            file_path_list.sort()
            self.__target_domain_file_path_list[i] = file_path_list

        if test_dir_list is not None and isinstance(test_dir_list, list) is False:
            raise TypeError("The type of `test_dir_list` must be `list`.")
        elif test_dir_list is None:
            test_dir_list = dir_list
            self.__test_file_path_list = self.__training_file_path_list
        else:
            test_dir_list.sort()
            self.__test_file_path_list = [None] * len(test_dir_list)
            for i in range(len(test_dir_list)):
                file_path_list = [test_dir_list[i] + "/" + file_name for file_name in os.listdir(test_dir_list[i] + "/")]
                file_path_list.sort()
                self.__test_file_path_list[i] = file_path_list

        self.__image_extractor = image_extractor
        self.__dir_list = dir_list
        self.__test_dir_list = test_dir_list
        self.__target_domain_dir_list = target_domain_dir_list

        self.iter_n = iter_n
        self.epochs = epochs
        self.batch_size = batch_size
        self.norm_mode = norm_mode
        self.scale = scale
        self.__noiseable_data = noiseable_data
        self.__ctx = ctx

    def generate_learned_samples(self):
        '''
        Draw and generate data.

        Returns:
            `Tuple` data. The shape is ...
            - `mxnet.ndarray` of observed data points in training.
            - `mxnet.ndarray` of supervised data in training.
            - `mxnet.ndarray` of observed data points in test.
            - `mxnet.ndarray` of supervised data in test.
            - `mxnet.ndarray` of obsrved data points in target domain.
        '''
        for _ in range(self.iter_n):
            training_batch_arr, test_batch_arr = None, None
            training_label_arr, test_label_arr = None, None
            target_domain_batch_arr = None
            for batch_size in range(self.batch_size):
                dir_key = np.random.randint(low=0, high=len(self.__training_file_path_list))

                training_one_hot_arr = torch.zeros((1, len(self.__training_file_path_list)), device=self.__ctx)
                training_one_hot_arr[0, dir_key] = 1

                file_key = np.random.randint(low=0, high=len(self.__training_file_path_list[dir_key]))
                training_data_arr = self.__image_extractor.extract(
                    path=self.__training_file_path_list[dir_key][file_key],
                )
                training_data_arr = self.pre_normalize(training_data_arr)

                test_dir_key = np.random.randint(low=0, high=len(self.__test_file_path_list))

                test_one_hot_arr = torch.zeros((1, len(self.__test_file_path_list)), device=self.__ctx)
                test_one_hot_arr[0, test_dir_key] = 1

                file_key = np.random.randint(low=0, high=len(self.__test_file_path_list[test_dir_key]))
                test_data_arr = self.__image_extractor.extract(
                    path=self.__test_file_path_list[test_dir_key][file_key],
                )
                test_data_arr = self.pre_normalize(test_data_arr)

                target_domain_dir_key = np.random.randint(low=0, high=len(self.__target_domain_file_path_list))

                target_domain_one_hot_arr = torch.zeros((1, len(self.__target_domain_file_path_list)), device=self.__ctx)
                target_domain_one_hot_arr[0, target_domain_dir_key] = 1

                target_domain_file_key = np.random.randint(low=0, high=len(self.__target_domain_file_path_list[target_domain_dir_key]))
                target_domain_data_arr = self.__image_extractor.extract(
                    path=self.__target_domain_file_path_list[target_domain_dir_key][target_domain_file_key],
                )
                target_domain_data_arr = self.pre_normalize(target_domain_data_arr)

                training_data_arr = torch.unsqueeze(training_data_arr, dim=0)
                test_data_arr = torch.unsqueeze(test_data_arr, dim=0)
                target_domain_data_arr = torch.unsqueeze(target_domain_data_arr, dim=0)

                if training_batch_arr is not None:
                    training_batch_arr = torch.cat((training_batch_arr, training_data_arr), dim=0)
                else:
                    training_batch_arr = training_data_arr
                
                if test_batch_arr is not None:
                    test_batch_arr = torch.cat((test_batch_arr, test_data_arr), dim=0)
                else:
                    test_batch_arr = test_data_arr

                if training_label_arr is not None:
                    training_label_arr = torch.cat((training_label_arr, training_one_hot_arr), dim=0)
                else:
                    training_label_arr = training_one_hot_arr

                if test_label_arr is not None:
                    test_label_arr = torch.cat((test_label_arr, test_one_hot_arr), dim=0)
                else:
                    test_label_arr = test_one_hot_arr

                if target_domain_batch_arr is not None:
                    target_domain_batch_arr = torch.cat((target_domain_batch_arr, target_domain_data_arr), dim=0)
                else:
                    target_domain_batch_arr = target_domain_data_arr

            if self.__noiseable_data is not None:
                training_batch_arr = self.__noiseable_data.noise(training_batch_arr)
                target_domain_batch_arr = self.__noiseable_data.noise(target_domain_batch_arr)

            pretext_arr, pretext_label_arr = self.create_pretext_task_samples(target_domain_batch_arr)
            yield training_batch_arr.float(), training_label_arr.float(), test_batch_arr.float(), test_label_arr.float(), pretext_arr.float(), pretext_label_arr.float()

    def pre_normalize(self, arr):
        '''
        Normalize before observation.

        Args:
            arr:    Tensor.
        
        Returns:
            Tensor.
        '''
        if self.norm_mode == "min_max":
            if torch.max(arr) != torch.min(arr):
                n = 0.0
            else:
                n = 1e-08
            arr = (arr - torch.min(arr)) / (torch.max(arr) - torch.min(arr) + n)
        elif self.norm_mode == "z_score":
            std = torch.std(arr)
            if std == 0:
                std += 1e-08
            arr = (arr - torch.mean(arr)) / std

        arr = arr * self.scale
        return arr

    def generate_inferenced_samples(self):
        '''
        Draw and generate data.
        The targets will be drawn from all image file sorted in ascending order by file name.

        Returns:
            `Tuple` data. The shape is ...
            - `None`.
            - `None`.
            - `mxnet.ndarray` of observed data points in test.
            - file path.
        '''
        scan_file_path_list = []
        for dir_key in range(len(self.__test_file_path_list)):
            for file_key in range(len(self.__test_file_path_list[dir_key])):
                file_path = self.__test_file_path_list[dir_key][file_key]
                scan_file_path_list.append(file_path)

        import random
        random.shuffle(scan_file_path_list)

        test_batch_arr = None
        file_path_list = []
        for file_path in scan_file_path_list:
            test_data_arr = self.__image_extractor.extract(
                path=file_path,
            )
            test_data_arr = self.pre_normalize(test_data_arr)

            test_data_arr = torch.unsqueeze(test_data_arr, dim=0)
            if test_batch_arr is not None:
                test_batch_arr = torch.cat((test_batch_arr, test_data_arr), dim=0)
            else:
                test_batch_arr = test_data_arr

            file_path_list.append(file_path)

            if test_batch_arr.shape[0] == self.batch_size:
                test_batch_arr_ = test_batch_arr
                test_batch_arr = None
                _file_path_list = file_path_list
                file_path_list = []
                yield None, None, test_batch_arr_, _file_path_list
            elif test_batch_arr.shape[0] > self.batch_size:
                raise ValueError()

    @abstractmethod
    def create_pretext_task_samples(self, target_domain_batch_arr):
        '''
        Create samples for pretext_task.

        Args:
            target_domain_batch_arr:    `nd.ndarray` of samples in target domain.
        
        Returns:
            Tuple data. The shape is ...
            - pretext task samples.
            - pretext task labels.
        '''
        raise NotImplementedError()
