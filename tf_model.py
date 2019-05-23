import numpy as np
import tensorflow as tf
from sklearn.metrics import roc_auc_score, accuracy_score
import sys

def train(model, dataset, batch_size=128):
    sess = tf.get_default_session()
    epoch_size = dataset.n / batch_size
    losses = []

    sys.stdout.write("np.mean(losses):")
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

#ERW
# tf_model knows nothing about classes <-->angle relations
# operates on arrays which has dimension of num_classes
def total_train(pathOUT, model, data, args, emodel=None, batch_size=128, epochs=25):
    sess = tf.get_default_session()
    if emodel is None:
        emodel = model
    train_accs = []
    valid_accs = []

    # ERW
    # maximal sensitivity not defined in  multi-class case?
    # please reintroduce this option
    # max_perf = evaluate2(emodel, data.valid, filtered=True)
    # print max_perf

    for i in range(epochs):
        sys.stdout.write("\nEPOCH: %d \n" % (i + 1))
        loss = train(model, data.train, batch_size)

        if model.tloss == 'parametrized_sincos':
            data.unweightedtest.weight(None)
            x, p, weights, arg_maxs, popts = predictions(emodel, data.unweightedtest)
            np.save(pathOUT+'res_vec_pred.npy', p)
            np.save(pathOUT+'res_vec_labels.npy', arg_maxs)
            weights_to_test = [1, 3, 5, 7, 9]
            for w in weights_to_test:
                data.unweightedtest.weight(w)
                x, p, weights, arg_maxs, popts = predictions(emodel, data.unweightedtest)
                np.save(pathOUT+'res_vec_pred'+str(w)+'.npy', p)
                np.save(pathOUT+'res_vec_labels'+str(w)+'.npy', arg_maxs)

        if model.tloss == 'soft':
            train_acc, train_mse, train_l1_delta_w, train_l2_delta_w = evaluate(emodel, data.train, args, 100000, filtered=True)
            valid_acc, valid_mse, valid_l1_delta_w, valid_l2_delta_w = evaluate(emodel, data.valid, args, filtered=True)
            msg_str_0 = "TRAINING:     LOSS: %.3f \n" % (loss)
            msg_str_1 = "TRAINING:     ACCURACY: %.3f MSE: %.3f L1_delta_w: %.3f  L2_delta_w: %.3f \n" % (train_acc, train_mse, train_l1_delta_w, train_l2_delta_w)
            msg_str_2 = "VALIDATION:   ACCURACY: %.3f MSE  %.3f L1_delta_w: %.3f, L2_delta_w: %.3f \n" % (valid_acc, valid_mse, valid_l1_delta_w, valid_l2_delta_w)
            print msg_str_0
            print msg_str_1
            print msg_str_2
            tf.logging.info(msg_str_0)
            tf.logging.info(msg_str_1)
            tf.logging.info(msg_str_2)

            # ERW: they are not "labels" but calculated values of weights for a given class
            #      class is indexed by its phiCPmix value or range.
            # why filtering is not applied?
            # MS: Name "labels" corresponds to nomenclature used in classification task.
            # "Label: is vector of valid probality distribution. But calc_w name is also good.
            # Filtering fixed

            calc_w, preds_w = softmax_predictions(emodel, data.valid, filtered=True)

            #ERW
            # control print
            # print "softmax: calc_w", calc_w
            # print "softmax: preds_w", preds_w

            np.save(pathOUT+'softmax_calc_w.npy', calc_w)
            np.save(pathOUT+'softmax_preds_w.npy', preds_w)

            train_accs += [train_acc]
            valid_accs += [valid_acc]

    return train_accs, valid_accs


def predictions(model, dataset, at_most=None, filtered=False):
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

    return x, p, weights, arg_maxs, popts

# ERW
# why this class is not using filter?
# MS: Fixed
def softmax_predictions(model, dataset, at_most=None, filtered=False):
    sess = tf.get_default_session()
    x = dataset.x[dataset.mask]
    weights = dataset.weights[dataset.mask]
    filt = dataset.filt[dataset.mask]

    if at_most is not None:
        filt = filt[:at_most]
        weights = weights[:at_most]

    if filtered:
        weights = weights[filt == 1]

    preds = sess.run(model.preds, {model.x: x})

    return weights, preds


# ERW
# extended input objects of original class
# added functionality of storing output information, hard-coded filenames which should be avoided
# roc_auc_score is not calculated as it is multi-class classification
def evaluate(model, dataset, args, at_most=None, filtered=False):
    _, pred_w, calc_w, arg_maxs, popts = predictions(model, dataset, at_most, filtered)

    #ERW
    # control print
    # print "evaluate: calc_w", calc_w
    # print "evaluate: pred_w", pred_w

    num_classes = calc_w.shape[1]
    pred_arg_maxs = np.argmax(pred_w, axis=1)
    calc_arg_maxs = np.argmax(calc_w, axis=1)

    #ERW
    # control print
    # print "evaluate: calc_arg_maxs", calc_arg_maxs
    # print "evaluate: pred_arg_maxs", pred_arg_maxs


    # ERW bez sensu, nie mozna porownywac roznicy wag i roznicy phi !!!
    # MS: I don't agree. It's difference between calc and pred arg_maxs calculated in two different directions (and taken minimum)
    # For example difference between last and first class is 1 (not num_class-1)
    calc_pred_argmaxs_distances = np.min(
       np.stack(
           [np.abs(pred_arg_maxs-calc_arg_maxs), (num_classes - np.abs(pred_arg_maxs-calc_arg_maxs))]
       ), axis=0)

    # print np.abs(pred_arg_maxs - calc_arg_maxs)
    #ERW: correct that if abs(pred_arg_maxs - calc_arg_maxs) = num_class -1, abs(pred_arg_maxs - calc_arg_maxs) = 0
    # MS: If I understand correctly it works correctly before. Fixed.
    mse = np.mean(np.sqrt(np.sum(calc_pred_argmaxs_distances**2, axis=1)))

    # Accuracy: average that most probable predicted class match most probable class
    # delta_class should be a variable in args
    delta_class = args.DATA_CLASS_DISTANCE
    accuracy = (calc_pred_argmaxs_distances <= delta_class).mean()
    l1_delta_w = np.mean(np.abs(calc_w - pred_w))
    l2_delta_w = np.sqrt(np.mean((calc_w - pred_w)**2))
    return accuracy, mse, l1_delta_w, l2_delta_w

# ERW
# removed class evaluate2. Why??


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
        # explain if option "soft" is a simple extension of what was implemented
        # previously for binary classification
        # MS Yes, it is
        if tloss == "soft":
            sx = linear(x, "regression", num_classes)
            self.preds = tf.nn.softmax(sx)
            #self.p = preds[:, 0] / (preds[:, 0] + preds[:, 1])
            self.p = self.preds

            # wa = p_a / p_c
            # wb = p_b / p_c
            # wa + wb + 1 = (p_a + p_b + p_c) / p_c
            # wa / (wa + wb + 1) = p_a / (p_a + p_b + p_c)
            #ERW
            # explain the line below
            # MS Sum of labels has to be equal one. So weights of each event are divided by their sum
            labels = weights / tf.tile(tf.reshape(tf.reduce_sum(weights, axis=1), (-1, 1)), (1, num_classes))
            self.loss = loss = tf.nn.softmax_cross_entropy_with_logits(logits=sx, labels=labels)
        elif tloss == "regr":
            sx = linear(x, "regr", 1)
            self.sx = sx
            self.loss = loss = tf.losses.mean_squared_error(self.arg_maxs, sx[:, 0])
        elif tloss == "popts":
            sx = linear(x, "regr", 3)
            self.sx = sx
            self.p = sx
            self.loss = loss = tf.losses.mean_squared_error(self.popts, sx)
        elif tloss == "parametrized_sincos":
            sx = linear(x, "regr", 2)

            if activation == 'tanh':
                sx = tf.nn.tanh(sx)
            elif activation == 'clip':
                sx = tf.clip_by_value(sx, -1., 1.)
            elif activation == 'mixed_clip':
                a = tf.clip_by_value(sx[:, 0], 0., 1.)
                b = tf.clip_by_value(sx[:, 1], -1., 1.)
                sx = tf.stack((a, b), axis=1)
            elif activation == 'linear':
                pass

            self.sx = sx
            self.p = sx
            self.loss = loss = tf.losses.huber_loss(tf.stack([self.arg_maxs, self.arg_maxs], axis=1), sx, delta=0.3)

        else:
            raise ValueError("tloss unrecognized: %s" % tloss)

        optimizer = {"GradientDescentOptimizer": tf.train.GradientDescentOptimizer, 
        "AdadeltaOptimizer": tf.train.AdadeltaOptimizer, "AdagradOptimizer": tf.train.AdagradOptimizer,
        "ProximalAdagradOptimizer": tf.train.ProximalAdagradOptimizer, "AdamOptimizer": tf.train.AdamOptimizer,
        "FtrlOptimizer": tf.train.FtrlOptimizer, "RMSPropOptimizer": tf.train.RMSPropOptimizer,
        "ProximalGradientDescentOptimizer": tf.train.ProximalGradientDescentOptimizer}[optimizer]
        self.train_op = optimizer(lr).minimize(loss)

