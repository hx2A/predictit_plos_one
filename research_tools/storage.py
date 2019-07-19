import os
import pickle


def save(name, data):
    filename = os.path.join('data', name + '.p')
    print('Writing data to ' + filename)
    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def save_all(name_data_pairs):
    for name, data in name_data_pairs:
        save(name, data)


def retrieve(name):
    filename = os.path.join('data', name + '.p')
    print('Reading data from ' + filename)
    with open(filename, 'rb') as f:
        return pickle.load(f)


def retrieve_all(names):
    return [retrieve(n) for n in names]
