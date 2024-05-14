Fill between 3D lines
---------------------

The `.Axes.fill_between` method has been extended to 3D, allowing to fill the
surface between two 3D lines with polygons through the `.Axes3D.fill_between`
function.

.. plot::
    :include-source:
    :alt: Example of fill_between

    N = 50
    theta = np.linspace(0, 2*np.pi, N)

    xs1 = np.cos(theta)
    ys1 = np.sin(theta)
    zs1 = 0.1 * np.sin(6 * theta)

    xs2 = 0.6 * np.cos(theta)
    ys2 = 0.6 * np.sin(theta)
    zs2 = 2  # Note that scalar values work in addition to length N arrays

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.fill_between(xs1, ys1, zs1, xs2, ys2, zs2,
                    alpha=0.5, edgecolor='k')
