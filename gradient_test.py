import numpy as np
import matplotlib.pyplot as plt

#define data
x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
y = np.array([20,18,16,24,12,10,8,7,6,5,4,3,2])

#find line of best fit
a, b = np.polyfit(x, y, 1)

print(a)

