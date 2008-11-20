"""
Illustrate some helper functions for shading regions where a logical
mask is True
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as collections


t = np.arange(0.0, 2, 0.01)
s = np.sin(2*np.pi*t)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_title('using fill_between_masked')
ax.plot(t, s, '-')
ax.axhline(0, color='black', lw=2)

collection = collections.PolyCollection.fill_between_masked(t, s, s>=0, yboundary=0, color='green', alpha=0.5)
ax.add_collection(collection)

collection = collections.PolyCollection.fill_between_masked(t, s, s<=0, yboundary=0, color='red', alpha=0.5)
ax.add_collection(collection)


fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_title('using span_masked')
ax.plot(t, s, '-')
ax.axhline(0, color='black', lw=2)

collection = collections.BrokenBarHCollection.span_masked(t, s>0, ymin=0, ymax=1, facecolor='green', alpha=0.5)
ax.add_collection(collection)

collection = collections.BrokenBarHCollection.span_masked(t, s<0, ymin=-1, ymax=0, facecolor='red', alpha=0.5)
ax.add_collection(collection)



plt.show()





