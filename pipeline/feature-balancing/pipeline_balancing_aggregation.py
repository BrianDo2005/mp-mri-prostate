"""This pipeline is intended to make the classification of ALL modality
features."""
from __future__ import division

import os
import numpy as np

from sklearn.externals import joblib
from sklearn.preprocessing import label_binarize
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.feature_selection import f_classif

from imblearn import under_sampling
from imblearn import over_sampling

from protoclass.data_management import GTModality

# Define the path where the patients are stored
path_patients = '/data/prostate/experiments'
# Define the path where the features have been extracted
path_features = '/data/prostate/extraction/mp-mri-prostate'
# Define a list of the path where the feature are kept
all_features = ['dct-t2w', 'edge-t2w/kirsch', 'edge-t2w/laplacian',
                'edge-t2w/prewitt', 'edge-t2w/scharr', 'edge-t2w/sobel',
                'gabor-t2w', 'harlick-t2w', 'ise-t2w', 'lbp-t2w', 'lbp-t2w',
                'phase-congruency-t2w',
                'dct-adc', 'edge-adc/kirsch', 'edge-adc/laplacian',
                'edge-adc/prewitt', 'edge-adc/scharr', 'edge-adc/sobel',
                'gabor-adc', 'harlick-adc', 'ise-adc', 'lbp-adc', 'lbp-adc',
                'phase-congruency-adc',
                'mrsi-spectra',
                'ese-dce',
                'spatial-position-euclidean', 'spatial-dist-center',
                'spatial-dist-contour']
# Define the extension of each features
ext_features = ['_dct_t2w.npy', '_edge_t2w.npy', '_edge_t2w.npy',
                '_edge_t2w.npy', '_edge_t2w.npy', '_edge_t2w.npy',
                '_gabor_t2w.npy', '_haralick_t2w.npy', '_ise_t2w.npy',
                '_lbp_8_1_t2w.npy', '_lbp_16_2_t2w.npy',
                '_phase_congruency_t2w.npy',
                '_dct_adc.npy', '_edge_adc.npy', '_edge_adc.npy',
                '_edge_adc.npy', '_edge_adc.npy', '_edge_adc.npy',
                '_gabor_adc.npy', '_haralick_adc.npy', '_ise_adc.npy',
                '_lbp_8_1_adc.npy', '_lbp_16_2_adc.npy',
                '_phase_congruency_adc.npy',
                '_spectra_mrsi.npy',
                '_ese__dce.npy',
                '_spe.npy', '_spe.npy',
                '_spe.npy']

# Load the file containing the indices to select
# path_feat_sel = '/data/prostate/results/mp-mri-prostate/exp-5/select-model-percentile/idx_sel_feat.pkl'
# idx_feat_sel = joblib.load(path_feat_sel)

# Define the path of the ground for the prostate
path_gt = ['GT_inv/prostate', 'GT_inv/pz', 'GT_inv/cg', 'GT_inv/cap']
# Define the label of the ground-truth which will be provided
label_gt = ['prostate', 'pz', 'cg', 'cap']

# Define the path where to store the data
path_store = '/data/prostate/balanced/mp-mri-prostate/exp-3'

N_JOBS = -1
# Create the under_samplers and over_samplers list to use
samplers = [under_sampling.InstanceHardnessThreshold(
                n_jobs=N_JOBS, estimator='random-forest'),
            under_sampling.NearMiss(version=1, n_jobs=N_JOBS),
            under_sampling.NearMiss(version=2, n_jobs=N_JOBS),
            under_sampling.NearMiss(version=3, n_jobs=N_JOBS),
            over_sampling.SMOTE(kind='regular', n_jobs=N_JOBS),
            over_sampling.SMOTE(kind='borderline1', n_jobs=N_JOBS),
            over_sampling.SMOTE(kind='borderline2', n_jobs=N_JOBS)]

# Define the sub-folder to use
sub_folder = ['iht', 'nm1', 'nm2', 'nm3', 'smote',
              'smote-b1', 'smote-b2']

# Generate the different path to be later treated
path_patients_list_gt = []
# Create the generator
id_patient_list = [name for name in os.listdir(path_patients)
                   if os.path.isdir(os.path.join(path_patients, name))]
# Sort the list of patient
id_patient_list = sorted(id_patient_list)

for id_patient in id_patient_list:
    # Append for the GT data - Note that we need a list of gt path
    path_patients_list_gt.append([os.path.join(path_patients, id_patient, gt)
                                  for gt in path_gt])

# Load all the data once. Splitting into training and testing will be done at
# the cross-validation time
data = []
label = []
for idx_pat in range(len(id_patient_list)):
    print 'Read patient {}'.format(id_patient_list[idx_pat])

    # Create the corresponding ground-truth
    gt_mod = GTModality()
    gt_mod.read_data_from_path(label_gt,
                               path_patients_list_gt[idx_pat])
    print 'Read the GT data for the current patient ...'

    # Let's get the information about the pz
    roi_prostate = gt_mod.extract_gt_data('prostate', output_type='index')
    # Get the label of the gt only for the prostate ROI
    gt_pz = gt_mod.extract_gt_data('pz', output_type='data')
    gt_pz = gt_pz[roi_prostate]

    # For each patient we nee to load the different feature
    patient_data = []
    for idx_feat in range(len(all_features)):
        # Create the path to the patient file
        filename_feature = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                            ext_features[idx_feat])
        path_data = os.path.join(path_features, all_features[idx_feat],
                                 filename_feature)
        single_feature_data = np.load(path_data)
        # Check if this is only one dimension data
        if len(single_feature_data.shape) == 1:
            single_feature_data = np.atleast_2d(single_feature_data).T
        patient_data.append(single_feature_data)

    # Add the information about the pz
    patient_data.append(np.atleast_2d(gt_pz).T)
    # Concatenate the data in a single array
    patient_data = np.concatenate(patient_data, axis=1)
    # Select the most important feature
    # patient_data = patient_data[:, idx_feat_sel]

    print 'Read all features ...'

    # Concatenate the training data
    data = patient_data
    # Extract the corresponding ground-truth for the testing data
    # Get the index corresponding to the ground-truth
    gt_cap = gt_mod.extract_gt_data('cap', output_type='data')
    label = gt_cap[roi_prostate]
    print 'Data and label extracted for the current patient ...'

    print 'Let s go for the different imbalancing methods'

    print data.shape
    print label.shape

    for idx_s, imb_method in enumerate(samplers):

        print 'Apply balancing {} over {}'.format(idx_s + 1, len(samplers))

        # Make the fitting and sampling
        data_resampled, label_resampled = imb_method.fit_sample(data, label)

        # Store the resampled data
        path_bal = os.path.join(path_store, sub_folder[idx_s])
        if not os.path.exists(path_bal):
            os.makedirs(path_bal)
        pat_chg = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                   '_aggregation.npz')
        filename = os.path.join(path_bal, pat_chg)
        np.savez(filename, data_resampled=data_resampled,
                 label_resampled=label_resampled)
        print 'Store the data'
