import numpy as np
import tensorflow as tf
from sklearn.metrics import roc_auc_score, accuracy_score
import sys

from src_py.metrics_utils import calculate_deltas_unsigned, calculate_deltas_signed

# Issue with regr_popts, not learning well after modifications of last weeks, last
# good production on June 20-th"

def train(model, dataset, batch_size=128):
    sess = tf.get_default_session()
    epoch_size = dataset.n / batch_size
    losses = []

    sys.stdout.write("<losses>):")
    for i in range(epoch_size):
        x, weights, arg_maxs, popts, filt,  = dataset.next_batch(batch_size)
        loss, _ = sess.run([model.loss, model.train_op],
                           {model.x: x, model.weights: weights, model.arg_maxs: arg_maxs, model.popts: popts})
        losses.append(loss)
        if i % (epoch_size / 10) == 5:
          sys.stdout.write(". %.3f " % np.mean(losses))
          losses =[]
          sys.stdout.flush()
    sys.stdout.write("\n")
    return np.mean(losses)

# ERW
# tf_model knows nothing about classes <-->angle relations
# operates on arrays which has dimention of num_classes
def total_train(pathOUT, model, data, args, emodel=None, batch_size=128, epochs=25):
    sess = tf.get_default_session()
    if emodel is None:
        emodel = model
    train_accs   = []
    valid_accs   = []
    test_accs    = []
    train_losses = []
    train_L1_deltas = []
    train_L2_deltas = []
    valid_L1_deltas = []
    valid_L2_deltas = []
    test_L1_deltas  = []
    test_L2_deltas  = []


    # ERW
    # maximal sensitivity not defined in  multi-class case?
    # please reintroduce this option
    # max_perf = evaluate2(emodel, data.valid, filtered=True)
    # print max_perf

    print "model = ", model.tloss

    for i in range(epochs):
        sys.stdout.write("\nEPOCH: %d \n" % (i + 1))
        train_loss = train(model, data.train, batch_size)
                
        if model.tloss == 'soft':
            train_acc, train_mean, train_l1_delta_w, train_l2_delta_w = evaluate(emodel, data.train, args, 100000, filtered=True)
            valid_acc, valid_mean, valid_l1_delta_w, valid_l2_delta_w = evaluate(emodel, data.valid, args, filtered=True)
            msg_str_0 = "TRAINING:     loss: %.3f \n" % (train_loss)
            msg_str_1 = "TRAINING:     acc: %.3f mean: %.3f L1_delta_w: %.3f  L2_delta_w: %.3f \n" % (train_acc, train_mean, train_l1_delta_w, train_l2_delta_w)
            msg_str_2 = "VALIDATION:   acc: %.3f mean  %.3f L1_delta_w: %.3f, L2_delta_w: %.3f \n" % (valid_acc, valid_mean, valid_l1_delta_w, valid_l2_delta_w)
            print msg_str_0
            print msg_str_1
            print msg_str_2
            tf.logging.info(msg_str_0)
            tf.logging.info(msg_str_1)
            tf.logging.info(msg_str_2)
            
            train_accs   += [train_acc]
            valid_accs   += [valid_acc]
            train_losses += [train_loss]
            
            train_L1_deltas += [train_l1_delta_w]
            train_L2_deltas += [train_l2_delta_w]
            valid_L1_deltas += [valid_l1_delta_w]
            valid_L2_deltas += [valid_l2_delta_w]

            if valid_acc == np.max(valid_accs):
                test_acc, test_mean, test_l1_delta_w, test_l2_delta_w = evaluate(emodel, data.test, args, filtered=True)
                msg_str_3 = "TESTING:      acc: %.3f mean  %.3f L1_delta_w: %.3f, L2_delta_w: %.3f \n" % (test_acc, test_mean, test_l1_delta_w, test_l2_delta_w)
                print msg_str_3
                tf.logging.info(msg_str_3)
                
                test_accs += [test_acc]
                test_L1_deltas += [test_l1_delta_w]
                test_L2_deltas += [test_l2_delta_w]

                calc_w, preds_w = softmax_predictions(emodel, data.test, filtered=True)

                # calc_w, preds_w normalisation to probability
                calc_w = calc_w / np.sum(calc_w, axis=1)[:, np.newaxis]
                preds_w = preds_w / np.sum(preds_w, axis=1)[:, np.newaxis]

                # ERW
                # control print
                # print "ERW test on softmax: calc_w \n"
                # print calc_w
                # print "ERW test on softmax: preds_w \n"
                # print preds_w
                np.save(pathOUT+'softmax_calc_w.npy', calc_w)
                np.save(pathOUT+'softmax_preds_w.npy', preds_w)


        if model.tloss == 'regr_popts':

            train_losses += [train_loss]
            msg_str = "TRAINING:     LOSS: %.3f \n" % (train_loss)
            print msg_str

            valid_calc_popts, valid_pred_popts = regr_popts_predictions(emodel, data.valid, filtered=True)
            np.save(pathOUT + 'valid_regr_calc_popts.npy', valid_calc_popts)
            np.save(pathOUT + 'valid_regr_preds_popts.npy', valid_pred_popts)

            test_calc_popts, test_pred_popts = regr_popts_predictions(emodel, data.test, filtered=True)
            np.save(pathOUT + 'test_regr_calc_popts.npy', test_calc_popts)
            np.save(pathOUT + 'test_regr_preds_popts.npy', test_pred_popts)

                
    if model.tloss == 'soft':
        test_roc_auc(preds_w, calc_w)             

        # storing history of training            
        np.save(pathOUT+'train_losses.npy', train_losses)
        print "train_losses", train_losses

        np.save(pathOUT+'train_accs.npy', train_accs )
        print "train_accs", train_accs
        np.save(pathOUT+'valid_accs.npy', valid_accs )
        print "valid_accs", valid_accs
        np.save(pathOUT+'test_accs.npy', test_accs )
        print "test_accs", test_accs

        np.save(pathOUT+'train_L1_deltas.npy', train_L1_deltas )
        print "train_L1_deltas", train_L1_deltas
        np.save(pathOUT+'valid_L1_deltas.npy', valid_L1_deltas )
        print "valid_L1_deltas", valid_L1_deltas
        np.save(pathOUT+'test_L1_deltas.npy', test_L1_deltas )
        print "test_L1_deltas", test_L1_deltas

        np.save(pathOUT+'train_L2_deltas.npy', train_L2_deltas )
        print "train_L2_deltas", train_L2_deltas
        np.save(pathOUT+'valid_L2_deltas.npy', valid_L2_deltas )
        print "valid_L2_deltas", valid_L2_deltas
        np.save(pathOUT+'test_L2_deltas.npy', test_L2_deltas )
        print "test_L2_deltas", test_L2_deltas

                 
    if model.tloss == 'regr_popts':

        # storing history of training            
        np.save(pathOUT+'train_losses.npy', train_losses)
        print "train_losses", train_losses
   
    return train_accs, valid_accs, test_accs



def predictions(model, dataset, at_most=None, filtered=True):
    sess = tf.get_default_session()
    x = dataset.x[dataset.mask]
    weights = dataset.weights[dataset.mask]
    filt = dataset.filt[dataset.mask]
    arg_maxs = dataset.arg_maxs[dataset.mask]
    popts = dataset.popts[dataset.mask]

    if at_most is not None:
      filt = filt[:at_most]
      x = x[:at_most]
      weights = weights[:at_most]
      arg_maxs = arg_maxs[:at_most]

    p = sess.run(model.p, {model.x: x})

    if filtered:
      p = p[filt == 1]
      x = x[filt == 1]
      weights = weights[filt == 1]
      arg_maxs = arg_maxs[filt == 1]

    # ERW
    # problem with consistency, p is normalised to unity, but weights are not!!
    # leads to wrong estimate of the L1, L2 metrics

    return x, p, weights, arg_maxs, popts

def softmax_predictions(model, dataset, at_most=None, filtered=True):
    sess = tf.get_default_session()
    x = dataset.x[dataset.mask]
    weights = dataset.weights[dataset.mask]
    filt = dataset.filt[dataset.mask]
    
    if at_most is not None:
        filt = filt[:at_most]
        weights = weights[:at_most]
        x = x[:at_most]

    if filtered:
        weights = weights[filt == 1]
        x = x[filt == 1]

    preds = sess.run(model.preds, {model.x: x})

    return weights, preds


#prepared by Michal
def calculate_classification_metrics(pred_w, calc_w, args):

    num_classes = calc_w.shape[1]
    # normalising calc_w to probabilities
    calc_w = calc_w / np.tile(np.reshape(np.sum(calc_w, axis=1), (-1, 1)), (1, num_classes))
    pred_arg_maxs = np.argmax(pred_w, axis=1)
    calc_arg_maxs = np.argmax(calc_w, axis=1)
    calc_pred_argmaxs_abs_distances = calculate_deltas_unsigned(pred_arg_maxs, calc_arg_maxs, num_classes)
    calc_pred_argmaxs_signed_distances = calculate_deltas_unsigned(pred_arg_maxs, calc_arg_maxs, num_classes)
    # Accuracy: average that most probable predicted class match most probable class
    # delta_class for matching  should be a variable in args
    delt_max = args.DELT_CLASSES
    acc = (calc_pred_argmaxs_abs_distances <= delt_max).mean()

    mean = np.mean(calc_pred_argmaxs_signed_distances)
    l1_delta_w = np.mean(np.abs(calc_w - pred_w)) / num_classes
    l2_delta_w = np.sqrt(np.mean((calc_w - pred_w) ** 2)) / num_classes

    return np.array([acc, mean, l1_delta_w, l2_delta_w])

#prepared by Michal
def regr_popts_predictions(model, dataset, at_most=None, filtered=True):
    sess = tf.get_default_session()
    x = dataset.x[dataset.mask]
    calc_popts = dataset.popts[dataset.mask]
    filt = dataset.filt[dataset.mask]

    if at_most is not None:
        filt = filt[:at_most]
        calc_popts = calc_popts[:at_most]
        x = x[:at_most]

    if filtered:
        calc_popts = calc_popts[filt == 1]
        x = x[filt == 1]

    pred_popts = sess.run(model.p, {model.x: x})
    return calc_popts, pred_popts



#prepared by Michal
def evaluate_test(model, dataset, args, at_most=None, filtered=True):
    _, pred_w, calc_w, arg_maxs, popts = predictions(model, dataset, at_most, filtered)

    pred_w = calc_w  # Assume for tests that calc_w equals calc_w
    return calculate_classification_metrics(pred_w, calc_w, args)

#prepared by Michal
def calculate_roc_auc(pred_w, calc_w, index_a, index_b):
    n, num_classes = calc_w.shape
    true_labels = np.concatenate([np.ones(n), np.zeros(n)])
    preds = np.concatenate([pred_w[:, index_a], pred_w[:, index_a]])
    weights = np.concatenate([calc_w[:, index_a], calc_w[:, index_b]])

    return roc_auc_score(true_labels, preds, sample_weight=weights)


def test_roc_auc(preds_w, calc_w):
    n, num_classes = calc_w.shape
    for i in range(0, num_classes):
         print(i+1, 'oracle_roc_auc: {}'.format(calculate_roc_auc(calc_w, calc_w, 0, i)),
                  'roc_auc: {}'.format(calculate_roc_auc(preds_w, calc_w, 0, i)))
 
def evaluate(model, dataset, args, at_most=None, filtered=True):
    _, pred_w, calc_w, arg_maxs, popts = predictions(model, dataset, at_most, filtered)

    # normalise calc_w to probabilities
    num_classes = calc_w.shape[1]
    calc_w = calc_w / np.tile(np.reshape(np.sum(calc_w, axis=1), (-1, 1)), (1, num_classes))

    pred_arg_maxs = np.argmax(pred_w, axis=1)
    calc_arg_maxs = np.argmax(calc_w, axis=1)
    calc_pred_argmaxs_abs_distances = calculate_deltas_unsigned(pred_arg_maxs, calc_arg_maxs, num_classes)
    calc_pred_argmaxs_signed_distances = calculate_deltas_signed(pred_arg_maxs, calc_arg_maxs, num_classes)

    mean = np.mean(calc_pred_argmaxs_signed_distances)

    # acc: average that most probable predicted class match most probable class
    #      within tolerance of delt_max
    delt_max = args.DELT_CLASSES
    acc = (calc_pred_argmaxs_abs_distances <= delt_max).mean()
      
    l1_delt_w = np.mean(np.abs(calc_w - pred_w))
    l2_delt_w = np.sqrt(np.mean((calc_w - pred_w)**2))
    
    return acc, mean, l1_delt_w, l2_delt_w

# ERW
# evaluate_oracle and  evaluate_preds has to be still
# implemented for multi-class classification.
# VERY IMPORTANT CLOSURE TEST

def evaluate_oracle(model, dataset, at_most=None, filtered=True):
    _, ps, was, wbs = predictions(model, dataset, at_most, filtered)
    return evaluate_preds(was/(was+wbs), was, wbs)

def evaluate_preds(preds, wa, wb):
    n = len(preds)
    true_labels = np.concatenate([np.ones(n), np.zeros(n)])
    preds = np.concatenate([preds, preds])
    weights = np.concatenate([wa, wb])

    return roc_auc_score(true_labels, preds, sample_weight=weights)


def linear(x, name, size, bias=True):
    w = tf.get_variable(name + "/W", [x.get_shape()[1], size])
    b = tf.get_variable(name + "/b", [1, size],
                        initializer=tf.zeros_initializer())
    return tf.matmul(x, w)  # + b vanishes in batch normalization


def batch_norm(x, name):
    mean, var = tf.nn.moments(x, [0])
    normalized_x = (x - mean) * tf.rsqrt(var + 1e-8)
    gamma = tf.get_variable(name + "/gamma", [x.get_shape()[-1]], initializer=tf.constant_initializer(1.0))
    beta = tf.get_variable(name + "/beta", [x.get_shape()[-1]])
    return gamma * normalized_x + beta


class NeuralNetwork(object):

    def __init__(self, num_features, num_classes, num_layers=1, size=100, lr=1e-3, keep_prob=1.0,
                 tloss="soft", activation='linear', input_noise=0.0, optimizer="AdamOptimizer"):
        batch_size = None
        self.x = x = tf.placeholder(tf.float32, [batch_size, num_features])
        self.weights = weights = tf.placeholder(tf.float32, [batch_size, num_classes])
        self.arg_maxs = tf.placeholder(tf.float32, [batch_size])
        self.popts = tf.placeholder(tf.float32, [batch_size, 3])
        self.tloss = tloss

        if input_noise > 0.0:
          x = x * tf.random_normal(tf.shape(x), 1.0, input_noise)

        for i in range(num_layers):
            x = tf.nn.relu(batch_norm(linear(x, "linear_%d" % i, size), "bn_%d" % i)) 
            if keep_prob < 1.0:
              x = tf.nn.dropout(x, keep_prob)
        #ERW
        # tloss ==  "soft" is a simple extension of what was implemented
        # previously as binary classification
        if tloss == "soft":
            sx = linear(x, "classes", num_classes)
            self.preds = tf.nn.softmax(sx)
            #self.p = preds[:, 0] / (preds[:, 0] + preds[:, 1])
            self.p = self.preds
            
            # labels: class probabilities, calculated as normalised weighs (probabilities)
            labels = weights / tf.tile(tf.reshape(tf.reduce_sum(weights, axis=1), (-1, 1)), (1,num_classes))
            self.loss = loss = tf.nn.softmax_cross_entropy_with_logits(logits=sx, labels=labels)
        elif tloss == "regr":
            sx = linear(x, "regr", 1)
            self.sx = sx
            self.loss = loss = tf.losses.mean_squared_error(self.arg_maxs, sx[:, 0])
        elif tloss == "regr_popts":
            sx = linear(x, "regr", 3)
            self.sx = sx
            self.p = sx
            self.loss = loss = tf.losses.mean_squared_error(self.popts, sx)

        else:
            raise ValueError("tloss unrecognized: %s" % tloss)

        optimizer = {"GradientDescentOptimizer": tf.train.GradientDescentOptimizer, 
        "AdadeltaOptimizer": tf.train.AdadeltaOptimizer, "AdagradOptimizer": tf.train.AdagradOptimizer,
        "ProximalAdagradOptimizer": tf.train.ProximalAdagradOptimizer, "AdamOptimizer": tf.train.AdamOptimizer,
        "FtrlOptimizer": tf.train.FtrlOptimizer, "RMSPropOptimizer": tf.train.RMSPropOptimizer,
        "ProximalGradientDescentOptimizer": tf.train.ProximalGradientDescentOptimizer}[optimizer]
        self.train_op = optimizer(lr).minimize(loss)

