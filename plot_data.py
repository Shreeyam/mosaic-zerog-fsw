import numpy as np
import matplotlib.pyplot as plt
import os

files = [f for f in os.listdir() if f.endswith(".npz")]

for f in files:
    data = np.load(f)['arr_0']
    print(data)
