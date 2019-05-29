import numpy as np
from glob import glob
import os, errno

import matplotlib.pyplot as plt


filelist_rhorho_Variant_4_1 = []

filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_2')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_4')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_6')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_8')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_10')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_12')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_14')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_16')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_18')
filelist_rhorho_Variant_4_1.append('npy/nn_rhorho_Variant-4.1_Unweighted_False_NO_NUM_CLASSES_20')

def calculate_metrics(directory, num_class):
    calc_w = np.load(os.path.join(directory, 'softmax_calc_w.npy'))
    preds_w = np.load(os.path.join(directory, 'softmax_preds_w.npy'))
    pred_arg_maxs = np.argmax(preds_w, axis=1)
    calc_arg_maxs = np.argmax(calc_w, axis=1)
    calc_pred_argmaxs_distances = np.min(
       np.stack(
           [np.abs(pred_arg_maxs-calc_arg_maxs), (num_class - np.abs(pred_arg_maxs-calc_arg_maxs))]
       ), axis=0)
    acc0 = (calc_pred_argmaxs_distances <= 0).mean()
    acc1 = (calc_pred_argmaxs_distances <= 1).mean()
    acc2 = (calc_pred_argmaxs_distances <= 2).mean()
    acc3 = (calc_pred_argmaxs_distances <= 3).mean()
    
    mse = np.mean(calc_pred_argmaxs_distances)
    l1_delta_w = np.mean(np.abs(calc_w - preds_w))
    l2_delta_w = np.sqrt(np.mean((calc_w - preds_w)**2))
    
    return np.array([acc0, acc1, acc2, acc3, mse, l1_delta_w, l2_delta_w])



metrics_Variant_4_1 = [calculate_metrics(filelist_rhorho_Variant_4_1[0], 2),  calculate_metrics(filelist_rhorho_Variant_4_1[1], 4),
           calculate_metrics(filelist_rhorho_Variant_4_1[1], 6), calculate_metrics(filelist_rhorho_Variant_4_1[2], 8),
           calculate_metrics(filelist_rhorho_Variant_4_1[3], 10), calculate_metrics(filelist_rhorho_Variant_4_1[3], 12),
           calculate_metrics(filelist_rhorho_Variant_4_1[4], 14), calculate_metrics(filelist_rhorho_Variant_4_1[4], 16),
           calculate_metrics(filelist_rhorho_Variant_4_1[4], 18), calculate_metrics(filelist_rhorho_Variant_4_1[4], 20)]
           
metrics_Variant_4_1 = np.stack(metrics_Variant_4_1)


# Now start plotting metrics
# Make better plots here, add axes labels, add color labels, store into figures/*.eps, figures/*.pdf files
# Should we first convert to histograms (?)

#---------------------------------------------------------------------

pathOUT = "figures/"
filename = "a1rho_Variant_4_1_acc_num_classes"

plt.plot(metrics_Variant_4_1[:, 0],'o', label='Acc0' )
plt.plot(metrics_Variant_4_1[:, 1],'o', label='Acc1')
plt.plot(metrics_Variant_4_1[:, 2],'o', label='Acc2')
plt.plot(metrics_Variant_4_1[:, 3],'o', label='Acc3')
plt.ylim([0.0, 1.3])
plt.legend()
plt.xlabel('Number of classes --->')
plt.ylabel('Accuracy')
plt.title('Feauture list: Variant-4.1')

ax = plt.gca()
plt.tight_layout()

if filename:
    try:
        os.makedirs(pathOUT)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    plt.savefig(pathOUT + filename+".eps")
    plt.savefig(pathOUT + filename+".pdf")
else:
    plt.show()

#---------------------------------------------------------------------
plt.show()
#---------------------------------------------------------------------

pathOUT = "figures/"
filename = "a1rho_Variant_4_1_mse_num_classes"

plt.plot(metrics_Variant_4_1[:, 4],'o', label='MSE')

plt.ylim([0.0, 3.0])
plt.legend()
plt.xlabel('Number of classes --->')
plt.ylabel('MSE')
plt.title('Feauture list: Variant-4.1')

ax = plt.gca()
plt.tight_layout()

if filename:
    try:
        os.makedirs(pathOUT)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    plt.savefig(pathOUT + filename+".eps")
    plt.savefig(pathOUT + filename+".pdf")
else:
    plt.show()

#---------------------------------------------------------------------
plt.show()
#---------------------------------------------------------------------


pathOUT = "figures/"
filename = "a1rho_Variant_4_1_L1delt_num_classes"

plt.plot(metrics_Variant_4_1[:, 5],'o', label='L1 <delta w>')

plt.ylim([0.0, 1.5])
plt.legend()
plt.xlabel('Number of classes --->')
plt.ylabel('L1 <delta w>')
plt.title('Feauture list: Variant-4.1')

ax = plt.gca()
plt.tight_layout()

if filename:
    try:
        os.makedirs(pathOUT)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    plt.savefig(pathOUT + filename+".eps")
    plt.savefig(pathOUT + filename+".pdf")
else:
    plt.show()
    
#---------------------------------------------------------------------
plt.show()
#---------------------------------------------------------------------

pathOUT = "figures/"
filename = "a1rho_Variant_4_1_L2delt_num_classes"

plt.plot(metrics_Variant_4_1[:, 6],'o', label='L2 <delta w>')

plt.ylim([0.0, 2.0])
plt.legend()
plt.xlabel('Number of classes --->')
plt.ylabel('L2 <delta w>')
plt.title('Feauture list: Variant-4.1')

ax = plt.gca()
plt.tight_layout()

if filename:
    try:
        os.makedirs(pathOUT)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    plt.savefig(pathOUT + filename+".eps")
    plt.savefig(pathOUT + filename+".pdf")
else:
    plt.show()
#---------------------------------------------------------------------
plt.show()
#---------------------------------------------------------------------
 
