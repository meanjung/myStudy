import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def graph():
    data = pd.read_csv('output.csv', sep=',', header=None)
    arr = data.values
    # print(type(arr))
    # print(arr.T[0])
    time = arr.T[0]
    coverage = arr.T[1]
    plt.xlabel("time")
    plt.ylabel("branch coverage")
    plt.xticks([i for i in range(0, 25, 4)])
    plt.plot(time, coverage)
    plt.show()

if __name__=="__main__":
    graph()