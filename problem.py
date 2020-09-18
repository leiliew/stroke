import glob
import os
import numpy as np
import pandas as pd
import rampwf as rw
import scipy.sparse as sps
from nilearn.image import load_img
from sklearn.model_selection import StratifiedShuffleSplit

from rampwf.score_types import BaseScoreType

DATA_HOME = 'data'
RANDOM_STATE = 42

# Author: Maria Telenczuk <https://github.com/maikia>
# License: BSD 3 clause

class ImageLoader(object):
    """
    Load and image and optionally its segmented mask.
    In segmentation_classifier.py, both `fit` and `predict` take as input
    an instance of `ImageLoader`.
    ImageLoader is used in `fit` and `predict` to either load one 3d image
    and its corresponding segmented mask  (at training time), or one 3d image
    (at test time).
    Images are loaded by using the method `load`.
    Parameters
    ==========
    img_ids : ArrayContainer of int
        vector of image IDs to train on
         (it is named X_array to be coherent with the current API,
         but as said here, it does not represent the data itself,
         only image IDs) corresponding to images from the given .csv file
    folder : str
        folder where the data_file is
    data_file : str
        name of the .csv file, with Img id, it's corresponding patient Id
        (INDI Subject ID) and where this particular data stored
    n_classes : int
        Total number of classes.
    """

    def __init__(self, path, dir_name):
        """ dir_name: 'train' or 'test' """
        self.t1_name = 'T1.nii.gz'
        self.lesion_name = 'truth.nii.gz'

        self.dir_data = os.path.join(path, dir_name)
        self.list_subj_dirs= os.listdir(self.data_dir)

    def load(self, path_patient):
        """
        Load one image and its corresponding segmented mask (at training time),
        or one image (at test time).
        Parameters
        ==========
        path : string
            path to the image to load
        Returns
        =======
        either a tuple `(x, y)` or `x`, where:
            - x is a numpy array of shape (height, width, depth),
              and corresponds to the image of the requested `index`.
            - y is a numpy array of the same shape as x, however filled only
                with integers of n_classes
        At training time, `y` is given, and `load` returns
        a tuple (x, y).
        At test time, `y` is `None`, and `load` returns `x`.
        """
        if not os.path.exists(path):
            raise IndexError("path does not exist")

        path_t1 = os.path.join(path_patient, self.t1_name)
        x = load_img(t1_path).get_data()


        if self.run_type == 'train':
            path_lesion = os.path.join(path_patient, self.lesion_name)
            y = load_img(path_lesion).get_data()
            return x, y
        elif self.run_type == 'test':
            return x

    def __iter__(self):
        for subj_dir in range(self.list_subj_dirs):
            yield self.load(subj_dir)


# define the scores
class DiceCoeff(BaseScoreType):
    # Dice’s coefficient (DC), which describes the volume overlap between two
    # segmentations and is sensitive to the lesion size;
    is_lower_the_better = True
    minimum = 0.0
    maximum = 1.0

    def __init__(self, name='dice coeff', precision=3):
        self.name = name
        self.precision = precision

    def __call__(self, y_true_mask, y_pred_mask):
        score = _dice_coeff(y_true_mask, y_pred_mask)

    def _dice_coeff(self, y_true_mask, y_pred_mask)
        if (np.sum(y_pred)==0) & (np.sum(y_true) == 0):
            return 1
        else:
            dice = ((np.sum((y_pred==1)&(y_true==1))*2.0) /
                    (np.sum(y_pred) + np.sum(y_true))
        return dice

# TODO: other ideas:
# def average_symmetric_surface_distance(y_pred, y_true):
    # ASSD: denotes the average surface distance between two segmentations
    # 1. define the average surface distance (ASD)
    # - get all the surface voxels
    # 2. average over both directions
# def hausdorff_distance(y_pred, y_true):
    # a measure of the maximum surface distance, hence especially sensitive to
    # outliers maximum of all surface distances

problem_title = 'Stroke Lesion Segmentation'
#_target_column_name = 'species'
_prediction_label_names = [0, 1]
# A type (class) which will be used to create wrapper objects for y_pred
Predictions = rw.prediction_types.make_multiclass(
    label_names=_prediction_label_names)
# An object implementing the workflow
workflow = rw.workflows.Classifier()


# TODO: dice coefficient
# TODO: scoring on the time of calculations?
score_types = [
    rw.score_types.Accuracy(name='acc'),  # sklearn accuracy_score:
# In multilabel classification, this function computes subset accuracy:
# the set of labels predicted for a sample must exactly match the corresponding
# set of labels in y_true.
    rw.score_types.DiceCoeff(),
]

# cross validation
def get_cv(X, y):
    # TODO: correct
    cv = ShuffleSplit(n_splits=8, test_size=0.2, random_state=RANDOM_STATE)
    return cv.split(X, y)

def _read_data(path, dir_name):
    """
    Read and process data and labels.
    Parameters
    ----------
    path : path to directory that has 'data' subdir
    typ : {'train', 'test'}
    Returns
    -------
    X, y data
    """
    return ImageLoader(path, dir_name)

def get_train_data(path="."):
    return _read_data(path, 'train')

def get_test_data(path="."):
    return _read_data(path, 'test')


# import submissions.starting_kit.keras_segmentation_classifier as classifier
'''
class SimplifiedSegmentationClassifier(object):
    """
    SimplifiedSegmentationClassifier workflow.
    This workflow is used to train image segmentation tasks, typically when
    the dataset cannot be stored in memory. It is altered version of SimplifiedImageClassifier
    Submissions need to contain one file, which by default by is named
    segmentation_classifier.py (it can be modified by changing
    `workflow_element_names`).
    image_classifier.py needs an `SegmentationClassifier` class, which implements
    `fit` and `predict`, where both `fit` and `predict` take
    as input an instance of `ImageLoader`.
    Parameters
    ==========
    n_classes : int
    data_file : file in data/images/ with all the patient ids and in which Site dir they can be found
        Total number of classes.
    """

    def __init__(self, n_classes=[0,1], data_file='ATLAS_Meta-Data_Release_1.1_standard_mni.csv', workflow_element_names=['segmentation_classifier']):
        self.n_classes = n_classes
        self.element_names = workflow_element_names
        self.data_file = data_file

    def train_submission(self, module_path, patient_ids):
        """Train an image classifier.
        module_path : str
            module where the submission is. the folder of the module
            have to contain segmentation_classifier.py. (e.g. starting_kit)
        patient_idxs : ArrayContainer vector of int
             patient ids (as in the data/images/<self.data_file> file)
             which are to be used for training
        """

        # FIXME: when added to workflow add those lines:
        #segmentation_classifier = import_file(module_path, self.element_names[0])
        #clf = segmentation_classifier.SegmentationClassifier()
        clf = classifier.KerasSegmentationClassifier()
        # load image one by one
        #for patient_id in patient_idxs:
        #    X = self._read_brain_image(module_path, patient_id)
        #    y_true = self._read_stroke_segmentation(module_path, patient_id)
        #    fitit = clf.fit(X, y_true)
        #    del X
        #    del y_true
        #return clf

        img_loader = ImageLoader(
            patient_ids,
            #X_array[train_is], y_array[train_is],
            #folder=folder,
            n_classes=self.n_classes
        )
        clf.fit(img_loader)
        return clf

    def test_submission(self, module_path, trained_model, patient_idxs):
        """Test an image classifier.
        trained_model : tuple (function, Classifier)
            tuple of a trained model returned by `train_submission`.
        patient_idxs : ArrayContainer of int
            vector of image IDs to test on.
            (it is named X_array to be coherent with the current API,
             but as said here, it does not represent the data itself,
             only image IDs).
        """
        # get images one by one
        clf = trained_model

        dices = np.zeros(len(patient_idxs))
        # load image one by one
        for idx, patient_id in enumerate(patient_idxs):
            X = self._read_brain_image(module_path, patient_id)
            y_true = self._read_stroke_segmentation(module_path, patient_id)
            y_pred = clf.predict(X)
            dices[idx] = dice_coefficient(y_pred, y_true)
            del X
            del y_true
            del y_pred
        return dices
'''
'''
import os
from keras.layers.normalization import BatchNormalization
from keras.layers import Input, Conv3D, MaxPooling3D, Conv3DTranspose
from keras.layers import Concatenate
from keras import Model

def fit_simple():

    inputs = Input((197, 233, 189, 1))
    x = BatchNormalization()(inputs)
    # downsampling
    down1conv1 = Conv3D(2, (3, 3, 3), activation='relu', padding='same')(x)
    down1conv1 = Conv3D(2, (3, 3, 3), activation='relu', padding='same')(down1conv1)
    down1pool = MaxPooling3D((2, 2, 2))(down1conv1)
    #middle
    mid_conv1 = Conv3D(2, (3, 3, 3), activation='relu', padding='same')(down1pool)
    mid_conv1 = Conv3D(2, (3, 3, 3), activation='relu', padding='same')(mid_conv1)

    # upsampling
    up1deconv = Conv3DTranspose(2, (3, 3, 3), strides=(2,2,2), activation='relu')(mid_conv1)
    up1concat = Concatenate()([up1deconv, down1conv1])
    up1conv1 = Conv3D(2, (3,3,3), activation='relu', padding='same')(up1concat)
    up1conv1 = Conv3D(2, (3,3,3), activation='relu', padding='same')(up1conv1)
    output = Conv3D(1, (3,3,3), activation='softmax', padding='same')(up1conv1)

    model = Model(inputs=inputs, outputs=output)
    model.compile(optimizer='rmsprop',
                 loss='mean_squared_error',
                 metrics=['accuracy'])

    train_suffix='_LesionSmooth_*.nii.gz'
    train_id = get_train_data(path='.')
    brain_image = _read_brain_image('.', train_id[1])
    mask = _read_stroke_segmentation('.', train_id[1]) 

    #model.fit(brain_image[None, ..., None], mask[None, ..., None].astype(bool))
    #model.fit_on_batch
    #return model
    # train the network
    H = model.fit_generator(aug.flow(trainX, trainY, batch_size=BS),
	validation_data=(testX, testY), steps_per_epoch=len(trainX) // BS,
	epochs=EPOCHS)
'''