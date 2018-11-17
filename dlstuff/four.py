#!python
# _*_ coding=utf-8 _*_

import argparse
import code
import readline
import signal
import sys
import numpy as np
from keras.datasets import boston_housing
from keras import models
from keras import layers
import matplotlib.pyplot as plt
from keras.utils.np_utils import to_categorical

def SigHandler_SIGINT(signum, frame):
    print()
    sys.exit(0)

class Argparser(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--string", type=str, help="string")
        parser.add_argument("--bool", action="store_true", help="bool", default=False)
        parser.add_argument("--dbg", action="store_true", help="debug", default=False)
        self.args = parser.parse_args()

def build_model(train_data):
    model = models.Sequential()
    model.add(layers.Dense(64, activation="relu", input_shape=(train_data.shape[1],)))
    model.add(layers.Dense(64, activation="relu"))
    model.add(layers.Dense(1))
    model.compile(optimizer="rmsprop", loss="mse", metrics=["mae"])
    return model

def smooth_curve(points, factor=0.9):
    smoothed_points = []
    for point in points:
        if smoothed_points:
            previous = smoothed_points[-1]
            smoothed_points.append(previous*factor+point*(1-factor))
        else:
            smoothed_points.append(point)
    return smoothed_points

# write code here
def premain(argparser):
    signal.signal(signal.SIGINT, SigHandler_SIGINT)
    #here
    (train_data, train_targets), (test_data, test_targets) = boston_housing.load_data()
    print(type(train_data))
    mean = train_data.mean(axis=0)
    train_data -= mean
    std = train_data.std(axis=0)
    train_data /= std

    test_data -= mean
    test_data /= std

    k = 4
    num_epochs = 500
    num_val_samples = len(train_data) // k
    num_epochs = 100
    all_scores = []
    all_mae_histories = []

    for i in range(k):
        print("processing fold #", i)
        val_data = train_data[i*num_val_samples:(i+1)*num_val_samples]
        val_targets = train_targets[i*num_val_samples:(i+1)*num_val_samples]
        partial_train_data = np.concatenate(
                [train_data[:i*num_val_samples],
                    train_data[(i+1)*num_val_samples:]], axis=0)
        partial_train_targets = np.concatenate(
                [train_targets[:i*num_val_samples],
                    train_targets[(i+1)*num_val_samples:]], axis=0)
        model = build_model(train_data)
        history = model.fit(partial_train_data, partial_train_targets, validation_data=(val_data, val_targets), epochs=num_epochs, batch_size=1, verbose=0)
        val_mse, val_mae = model.evaluate(val_data, val_targets, verbose=0)
        mae_history = history.history["val_mean_absolute_error"]
        all_mae_histories.append(mae_history)
        all_scores.append(val_mae)

    average_mae_history = [np.mean([x[i] for x in all_mae_histories]) for i in range(num_epochs)]
    smoothed_mae_history = smooth_curve(average_mae_history[10:])
    plt.plot(range(1, len(smoothed_mae_history) + 1), smoothed_mae_history)
    plt.xlabel("Epochs")
    plt.ylabel("Validation MAE")
    plt.show()

def main():
    argparser = Argparser()
    if argparser.args.dbg:
        try:
            premain(argparser)
        except Exception as e:
            print(e.__doc__)
            if e.message: print(e.message)
            variables = globals().copy()
            variables.update(locals())
            shell = code.InteractiveConsole(variables)
            shell.interact(banner="DEBUG REPL")
    else:
        premain(argparser)

if __name__ == "__main__":
    main()
