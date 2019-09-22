import numpy as np
import os
from data_utils import read_np
from scipy import optimize


def weight_fun(x, a, b, c):
    return a + b * np.cos(x) + c * np.sin(x)

def hits_fun(classes, x, num_classes):

    hits = np.zeros(num_classes)
    for i in range(num_classes):
        if x >= classes[i] and  x < classes[i+1]:
             hits[i] = 1.0

    return hits


# here weights and arg_maxs are calculated from continuum distributions
def calc_weights_and_arg_maxs(classes, popts, data_len, num_classes):
    arg_maxs     = np.zeros((data_len, 1))
    weights      = np.zeros((data_len, num_classes))
    hits_argmaxs = np.zeros((data_len, num_classes))
    for i in range(data_len):
        weights[i] = weight_fun(classes, *popts[i])
        arg_max = 0
        if weight_fun(2 * np.pi, *popts[i]) > weight_fun(arg_max, *popts[i]):
            arg_max = 2 * np.pi
        phi = np.arctan(popts[i][2] / popts[i][1])

        if 0 < phi < 2 * np.pi and weight_fun(phi, *popts[i]) > weight_fun(arg_max, *popts[i]):
            arg_max = phi
        if 0 < phi + np.pi < 2 * np.pi and weight_fun(phi + np.pi, *popts[i]) > weight_fun(arg_max, *popts[i]):
            arg_max = phi + np.pi
        if 0 < phi + 2 * np.pi < 2 * np.pi and weight_fun(phi + 2 * np.pi, *popts[i]) > weight_fun(arg_max,
                                                                                                   *popts[i]):
            arg_max = phi + 2 * np.pi

        arg_maxs[i] = arg_max
        hits_argmaxs[i] = hits_fun(classes, arg_max, num_classes)

    return weights, arg_maxs, hits_argmaxs


def preprocess_data(args):
    data_path = args.IN
    num_classes = args.NUM_CLASSES
    reuse_weights = args.REUSE_WEIGHTS  # Set this flag to true if you want reuse calculated weights

    print "Loading data"
    suffix = (args.TYPE).split("_")[-1] #-1 to indeks ostatniego elementu 
    data = read_np(os.path.join(data_path, suffix + "_raw.data.npy"))
    w = read_np(os.path.join(data_path, suffix + "_raw.w.npy")).swapaxes(0, 1)
    perm = read_np(os.path.join(data_path, suffix + "_raw.perm.npy"))
    print "Read %d events" % data.shape[0]

    data_len = data.shape[0]
    classes = np.linspace(0, 2, num_classes) * np.pi

    if not os.path.exists(os.path.join(data_path, 'popts.npy')) or not os.path.exists(os.path.join(data_path, 'coeffs.npy')):
        coeffs = np.zeros((data_len, 3))
        popts  = np.zeros((data_len, 3))
        ccovs  = np.zeros((data_len, 3, 3))
        # here x correspond to values of CPmix at thich data were generated
        # coeffs is an array for C0, C1, C2 coefficients (per event)
        # popts is an array for  C0, C1, C2 coefficients shifted by+1.0, to avoid negative values
        # being inputs to regression or softmax 
        x = np.array([0, 0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2.0]) * np.pi
        for i in range(data_len):
            coeff, ccov = optimize.curve_fit(weight_fun, x, w[i, :], p0=[1, 1, 1])
            coeffs[i] = coeff
            popts[i]  = coeff
            ccovs[i]  = ccov

        np.save(os.path.join(data_path, 'popts.npy'), popts)
        np.save(os.path.join(data_path, 'coeffs.npy'), coeffs)
        np.save(os.path.join(data_path, 'ccovs.npy'), ccovs)
    popts = np.load(os.path.join(data_path, 'popts.npy'))
    coeffs = np.load(os.path.join(data_path, 'coeffs.npy'))

    if not reuse_weights or not os.path.exists(os.path.join(data_path, 'weights.npy')) \
            or not os.path.exists(os.path.join(data_path, 'arg_maxs.npy')) \
            or not os.path.exists(os.path.join(data_path, 'hits_argmaxs.npy')) \
            or np.load(os.path.join(data_path, 'weights.npy')).shape[1] != num_classes \
            or np.load(os.path.join(data_path, 'hits_argmaxs')).shape[1] != num_classes:
        weights, arg_maxs,  hits_argmaxs = calc_weights_and_arg_maxs(classes, coeffs, data_len, num_classes)
        np.save(os.path.join(data_path, 'weights.npy'), weights)
        np.save(os.path.join(data_path, 'arg_maxs.npy'), arg_maxs)
        np.save(os.path.join(data_path, 'hits_argmaxs.npy'), hits_argmaxs)
    weights  = np.load(os.path.join(data_path, 'weights.npy'))
    arg_maxs = np.load(os.path.join(data_path, 'arg_maxs.npy'))
    hits_argmaxs = np.load(os.path.join(data_path, 'hits_argmaxs.npy'))

    #ERW
    # here arg_maxs are in fraction of pi, not in the class index
    # how we go then from fraction of pi to class index??
    # print "preprocess: weights", weights
    # print "preprocess: arg_maxs", arg_maxs

    #ERW
    # I am not sure what the purpose is and if it make sens.
    if args.RESTRICT_MOST_PROBABLE_ANGLE:
        arg_maxs[arg_maxs > np.pi] = -1 * arg_maxs[arg_maxs > np.pi] + 2 * np.pi

    #ERW
    # this optimisation does not help, revisit, maybe not correctly implemented?
    if args.NORMALIZE_WEIGHTS:
        weights = weights/np.reshape(popts[:, 0], (-1, 1))
        
    # ERW    
    # here weights and arg_maxs are calculated at value of CPmix representing given class
    # in training, class is expressed as integer, not fraction pf pi.

    print "hits_argmaxs", hits_argmaxs
    return data, weights, arg_maxs, perm, popts, hits_argmaxs
