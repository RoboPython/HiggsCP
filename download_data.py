import os
import urllib

import numpy as np


def download_data(args):
    data_path = args.IN
    if os.path.exists(data_path) is False:
        os.mkdir(data_path)
    download_weights(args)
    download_data_files(args)


def download_weights(args):
    data_path = args.IN
    angles = ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20']
    weights = []
    output_weight_file = os.path.join(data_path, 'rhorho_raw.w.npy')
    if os.path.exists(output_weight_file) and not args.FORCE_DOWNLOAD:
        print 'Output weights file exists. Downloading data cancelled. ' \
              'If you want to force download use --force_download option'
        return
    for angle in angles:
        filename = 'rhorho_raw.w_' + angle + '.npy'
        print 'Donwloading ' + filename
        filepath = os.path.join(data_path, filename)
        urllib.urlretrieve(args.DATA_URL + filename, filepath)
        weights.append(np.load(filepath))
    weights = np.stack(weights)
    np.save(output_weight_file, weights)


def download_data_files(args):
    data_path = args.IN
    files = ['rhorho_raw.data.npy', 'rhorho_raw.perm.npy']
    for file in files:
        file_path = os.path.join(data_path, file)
        if os.path.exists(file_path) and not args.FORCE_DOWNLOAD:
            print 'File ' + file_path + ' exists. Downloading data cancelled. ' \
                  'If you want to force download use --force_download option'
        else:
            print 'Donwloading ' + file
            urllib.urlretrieve(args.DATA_URL + file, file_path)
