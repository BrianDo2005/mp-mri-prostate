"""This pipeline is intended to make the classification of ALL modality
features."""
from __future__ import division

import os
import numpy as np

from sklearn.externals import joblib
from sklearn.preprocessing import label_binarize

from sklearn.feature_selection import SelectKBest
from sklearn.feature_selection import f_classif
from sklearn.decomposition import FastICA

from sklearn.ensemble import RandomForestClassifier

from protoclass.data_management import GTModality

# Define the path where the patients are stored
path_patients = '/data/prostate/experiments'
# Define the path where the features have been extracted
path_features = '/data/prostate/extraction/mp-mri-prostate'

# T2W
t2w_features = ['dct-t2w', 'edge-t2w/kirsch', 'edge-t2w/laplacian',
                'edge-t2w/prewitt', 'edge-t2w/scharr', 'edge-t2w/sobel',
                'gabor-t2w', 'harlick-t2w', 'ise-t2w', 'lbp-t2w', 'lbp-t2w',
                'phase-congruency-t2w']
t2w_ext_features = ['_dct_t2w.npy', '_edge_t2w.npy', '_edge_t2w.npy',
                    '_edge_t2w.npy', '_edge_t2w.npy', '_edge_t2w.npy',
                    '_gabor_t2w.npy', '_haralick_t2w.npy', '_ise_t2w.npy',
                    '_lbp_8_1_t2w.npy', '_lbp_16_2_t2w.npy',
                    '_phase_congruency_t2w.npy']
t2w_feat_sel = '/data/prostate/results/mp-mri-prostate/exp-3/selection-extraction/anova/t2w/idx_sel_feat.pkl'
# Load the indices to select
t2w_feat_sel_idx = joblib.load(t2w_feat_sel)

# ADC
adc_features = ['dct-adc', 'edge-adc/kirsch', 'edge-adc/laplacian',
                'edge-adc/prewitt', 'edge-adc/scharr', 'edge-adc/sobel',
                'gabor-adc', 'harlick-adc', 'ise-adc', 'lbp-adc', 'lbp-adc',
                'phase-congruency-adc']
adc_ext_features = ['_dct_adc.npy', '_edge_adc.npy', '_edge_adc.npy',
                    '_edge_adc.npy', '_edge_adc.npy', '_edge_adc.npy',
                    '_gabor_adc.npy', '_haralick_adc.npy', '_ise_adc.npy',
                    '_lbp_8_1_adc.npy', '_lbp_16_2_adc.npy',
                    '_phase_congruency_adc.npy']
adc_feat_sel = '/data/prostate/results/mp-mri-prostate/exp-3/selection-extraction/rf/adc/idx_sel_feat.pkl'
# Load the indexes to select indices
adc_feat_sel_idx = joblib.load(adc_feat_sel)

# MRSI
mrsi_features = ['mrsi-spectra']
mrsi_ext_features = ['_spectra_mrsi.npy']

# DCE
dce_features = ['ese-dce']
dce_ext_features = ['_ese__dce.npy']

# Spatial information
spatial_features = ['spatial-position-euclidean', 'spatial-dist-center',
                    'spatial-dist-contour']
spatial_ext_features = ['_spe.npy', '_spe.npy',
                        '_spe.npy']

# Define the path of the ground for the prostate
path_gt = ['GT_inv/prostate', 'GT_inv/pz', 'GT_inv/cg', 'GT_inv/cap']
# Define the label of the ground-truth which will be provided
label_gt = ['prostate', 'pz', 'cg', 'cap']

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
data_t2w = []
data_adc = []
data_dce = []
data_mrsi = []
data_spatial = []
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

    # Read the T2W information
    patient_data_t2w = []
    for idx_feat in range(len(t2w_features)):
        # Create the path to the patient file
        filename_feature = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                            t2w_ext_features[idx_feat])
        path_data = os.path.join(path_features, t2w_features[idx_feat],
                                 filename_feature)
        single_feature_data = np.load(path_data)
        # Check if this is only one dimension data
        if len(single_feature_data.shape) == 1:
            single_feature_data = np.atleast_2d(single_feature_data).T
        patient_data_t2w.append(single_feature_data)

    # Concatenate the data
    patient_data_t2w = np.concatenate(patient_data_t2w, axis=1)
    data_t2w.append(patient_data_t2w)

    # Read the ADC information
    patient_data_adc = []
    for idx_feat in range(len(adc_features)):
        # Create the path to the patient file
        filename_feature = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                            adc_ext_features[idx_feat])
        path_data = os.path.join(path_features, adc_features[idx_feat],
                                 filename_feature)
        single_feature_data = np.load(path_data)
        # Check if this is only one dimension data
        if len(single_feature_data.shape) == 1:
            single_feature_data = np.atleast_2d(single_feature_data).T
        patient_data_adc.append(single_feature_data)

    # Concatenate the data
    patient_data_adc = np.concatenate(patient_data_adc, axis=1)
    data_adc.append(patient_data_adc)

    # Read the MRSI information
    patient_data_mrsi = []
    for idx_feat in range(len(mrsi_features)):
        # Create the path to the patient file
        filename_feature = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                            mrsi_ext_features[idx_feat])
        path_data = os.path.join(path_features, mrsi_features[idx_feat],
                                 filename_feature)
        single_feature_data = np.load(path_data)
        # Check if this is only one dimension data
        if len(single_feature_data.shape) == 1:
            single_feature_data = np.atleast_2d(single_feature_data).T
        patient_data_mrsi.append(single_feature_data)

    # Concatenate the data
    patient_data_mrsi = np.concatenate(patient_data_mrsi, axis=1)
    data_mrsi.append(patient_data_mrsi)

    # Read the DCE information
    patient_data_dce = []
    for idx_feat in range(len(dce_features)):
        # Create the path to the patient file
        filename_feature = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                            dce_ext_features[idx_feat])
        path_data = os.path.join(path_features, dce_features[idx_feat],
                                 filename_feature)
        single_feature_data = np.load(path_data)
        # Check if this is only one dimension data
        if len(single_feature_data.shape) == 1:
            single_feature_data = np.atleast_2d(single_feature_data).T
        patient_data_dce.append(single_feature_data)

    # Concatenate the data
    patient_data_dce = np.concatenate(patient_data_dce, axis=1)
    data_dce.append(patient_data_dce)

    # Read the SPATIAL information
    patient_data_spatial = []
    for idx_feat in range(len(spatial_features)):
        # Create the path to the patient file
        filename_feature = (id_patient_list[idx_pat].lower().replace(' ', '_') +
                            spatial_ext_features[idx_feat])
        path_data = os.path.join(path_features, spatial_features[idx_feat],
                                 filename_feature)
        single_feature_data = np.load(path_data)
        # Check if this is only one dimension data
        if len(single_feature_data.shape) == 1:
            single_feature_data = np.atleast_2d(single_feature_data).T
        patient_data_spatial.append(single_feature_data)

    # Add the information about the pz
    patient_data_spatial.append(np.atleast_2d(gt_pz).T)
    # Concatenate the data
    patient_data_spatial = np.concatenate(patient_data_spatial, axis=1)
    data_spatial.append(patient_data_spatial)

    # Extract the corresponding ground-truth for the testing data
    # Get the index corresponding to the ground-truth
    gt_cap = gt_mod.extract_gt_data('cap', output_type='data')
    label.append(gt_cap[roi_prostate])
    print 'Data and label extracted for the current patient ...'

# Create a list concatenating all the data
data = [data_t2w, data_adc, data_mrsi, data_dce, data_spatial]

result_cv = []
# Go for LOPO cross-validation
for idx_lopo_cv in range(len(id_patient_list)):

    # Display some information about the LOPO-CV
    print 'Round #{} of the LOPO-CV'.format(idx_lopo_cv + 1)

    # Load already the testing and training label
    testing_label = np.ravel(label_binarize(label[idx_lopo_cv], [0, 255]))
    training_label = [arr for idx_arr, arr in enumerate(label)
                      if idx_arr != idx_lopo_cv]
    training_label = np.ravel(label_binarize(
        np.hstack(training_label).astype(int), [0, 255]))


    # Load the data for each modality by selecting the featur of interest
    # T2W
    # Load data
    t2w_training_data = [arr for idx_arr, arr in enumerate(data[0])
                         if idx_arr != idx_lopo_cv]
    t2w_testing_data = data[0][idx_lopo_cv]
    # Convert the list to array
    t2w_training_data = np.concatenate(t2w_training_data, axis=0)
    t2w_testing_data = np.array(t2w_testing_data)
    # Select subset
    t2w_training_data = t2w_training_data[:, t2w_feat_sel_idx]
    t2w_testing_data = t2w_testing_data[:, t2w_feat_sel_idx]

    # ADC
    # Load data
    adc_training_data = [arr for idx_arr, arr in enumerate(data[1])
                         if idx_arr != idx_lopo_cv]
    adc_testing_data = data[1][idx_lopo_cv]
    # Convert the list to array
    adc_training_data = np.concatenate(adc_training_data, axis=0)
    adc_testing_data = np.array(adc_testing_data)
    # Select the subset
    adc_training_data = adc_training_data[:, adc_feat_sel_idx]
    adc_testing_data = adc_testing_data[:, adc_feat_sel_idx]

    # MRSI
    mrsi_training_data = [arr for idx_arr, arr in enumerate(data[2])
                         if idx_arr != idx_lopo_cv]
    mrsi_testing_data = data[2][idx_lopo_cv]
    # Convert the list to array
    mrsi_training_data = np.concatenate(mrsi_training_data, axis=0)
    mrsi_testing_data = np.array(mrsi_testing_data)

    # DCE
    # Load data
    dce_training_data = [arr for idx_arr, arr in enumerate(data[3])
                         if idx_arr != idx_lopo_cv]
    dce_testing_data = data[3][idx_lopo_cv]
    # Convert the list to array
    dce_training_data = np.concatenate(dce_training_data, axis=0)
    dce_testing_data = np.array(dce_testing_data)
    # Select the data
    # Learn the PCA projection
    ica = FastICA(n_components=24, whiten=True)
    dce_training_data = ica.fit_transform(dce_training_data)
    dce_testing_data = ica.transform(dce_testing_data)

    # Spatial information
    # Load data
    spa_training_data = [arr for idx_arr, arr in enumerate(data[4])
                         if idx_arr != idx_lopo_cv]
    spa_testing_data = data[4][idx_lopo_cv]
    # Convert the list to array
    spa_training_data = np.concatenate(spa_training_data, axis=0)
    spa_testing_data = np.array(spa_testing_data)

    # Stack all the training data and testing data
    training_data = np.hstack((t2w_training_data,
                               adc_training_data,
                               mrsi_training_data,
                               dce_training_data,
                               spa_training_data))
    testing_data = np.hstack((t2w_testing_data,
                               adc_testing_data,
                               mrsi_testing_data,
                               dce_testing_data,
                               spa_testing_data))

    # Perform the classification for the current cv and the
    # given configuration
    crf = RandomForestClassifier(n_estimators=100, n_jobs=-1)
    pred_prob = crf.fit(training_data,
                        np.ravel(training_label)).predict_proba(
                            testing_data)

    result_cv.append([pred_prob, crf.classes_])

# Save the information
path_store = '/data/prostate/results/mp-mri-prostate/exp-4/aggregation-modality'
if not os.path.exists(path_store):
    os.makedirs(path_store)
joblib.dump(result_cv, os.path.join(path_store,
                                    'results.pkl'))
