import numpy as np
from numpy.linalg import solve as ls

#declarar as matrizes
a = np.array([[1,1],[-3,1]])
b = np.array([[6],[2]])

x = ls(a,b)
print(x)