"""This pipeline is intended to make the classification of ALL modality
features."""
from __future__ import division

import os
import numpy as np

from sklearn.externals import joblib
from sklearn.preprocessing import label_binarize
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectPercentile
from sklearn.feature_selection import f_classif

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

    print 'Read all features ...'

    # Concatenate the training data
    data.append(patient_data)
    # Extract the corresponding ground-truth for the testing data
    # Get the index corresponding to the ground-truth
    gt_cap = gt_mod.extract_gt_data('cap', output_type='data')
    label.append(gt_cap[roi_prostate])
    print 'Data and label extracted for the current patient ...'

percentiles = np.array([1., 2., 5., 7.5, 10, 12.5, 15.])

results_p = []
for p in percentiles:

    result_cv = []
    # Go for LOPO cross-validation
    for idx_lopo_cv in range(len(id_patient_list)):

        # Display some information about the LOPO-CV
        print 'Round #{} of the LOPO-CV'.format(idx_lopo_cv + 1)

        # Get the testing data
        testing_data = data[idx_lopo_cv]
        testing_label = np.ravel(label_binarize(label[idx_lopo_cv], [0, 255]))
        print 'Create the testing set ...'

        # Create the training data and label
        training_data = [arr for idx_arr, arr in enumerate(data)
                         if idx_arr != idx_lopo_cv]
        training_label = [arr for idx_arr, arr in enumerate(label)
                          if idx_arr != idx_lopo_cv]
        # Concatenate the data
        training_data = np.vstack(training_data)
        training_label = np.ravel(label_binarize(
            np.hstack(training_label).astype(int), [0, 255]))
        print 'Create the training set ...'

        # Perform the classification for the current cv and the
        # given configuration
        sel = SelectPercentile(f_classif, p)
        training_data = sel.fit_transform(training_data, training_label)
        testing_data = sel.transform(testing_data)
        crf = RandomForestClassifier(n_estimators=100, n_jobs=-1)
        pred_prob = crf.fit(training_data, training_label).predict_proba(
            testing_data)

        result_cv.append([pred_prob, crf.classes_])

    results_p.append(result_cv)

# Save the information
path_store = '/data/prostate/results/mp-mri-prostate/exp-5/select-from-all'
if not os.path.exists(path_store):
    os.makedirs(path_store)
joblib.dump(results_p, os.path.join(path_store,
                                    'results.pkl'))
