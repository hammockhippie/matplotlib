# -*- encoding: utf-8 -*-

import os
import shutil
import numpy as np
import nose
from nose.plugins.skip import SkipTest
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.compat import subprocess
from matplotlib.testing.compare import compare_images, ImageComparisonFailure
from matplotlib.testing.decorators import _image_directories

baseline_dir, result_dir = _image_directories(lambda: 'dummy func')


def check_for(texsystem):
    header = r"""
    \documentclass{minimal}
    \usepackage{pgf}
    \begin{document}
    \typeout{pgfversion=\pgfversion}
    \makeatletter
    \@@end
    """
    try:
        latex = subprocess.Popen(["xelatex", "-halt-on-error"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
        stdout, stderr = latex.communicate(header.encode("utf8"))
    except OSError:
        return False

    return latex.returncode == 0


def switch_backend(backend):

    def switch_backend_decorator(func):
        def backend_switcher(*args, **kwargs):
            try:
                prev_backend = mpl.get_backend()
                mpl.rcdefaults()
                plt.switch_backend(backend)
                result = func(*args, **kwargs)
            finally:
                plt.switch_backend(prev_backend)
            return result

        return nose.tools.make_decorator(func)(backend_switcher)
    return switch_backend_decorator


def compare_figure(fname):
    actual = os.path.join(result_dir, fname)
    plt.savefig(actual)

    expected = os.path.join(result_dir, "expected_%s" % fname)
    shutil.copyfile(os.path.join(baseline_dir, fname), expected)
    err = compare_images(expected, actual, tol=10)
    if err:
        raise ImageComparisonFailure('images not close: %s vs. %s' % (actual, expected))

###############################################################################

def create_figure():
    plt.figure()
    x = np.linspace(0, 1, 15)
    plt.plot(x, x**2, "b-")
    plt.plot(x, 1-x**2, "g>")
    plt.plot([0.9], [0.5], "ro", markersize=3)
    plt.text(0.9, 0.5, u'unicode (ü, °, µ) and math ($\\mu_i = x_i^2$)', ha='right', fontsize=20)
    plt.ylabel(u'sans-serif with math $\\frac{\\sqrt{x}}{y^2}$..', family='sans-serif')


# test compiling a figure to pdf with xelatex
@switch_backend('pgf')
def test_xelatex():
    if not check_for('xelatex'):
        raise SkipTest('xelatex + pgf is required')

    rc_xelatex = {'font.family': 'serif',
                   'pgf.rcfonts': False,}
    mpl.rcParams.update(rc_xelatex)
    create_figure()
    compare_figure('pgf_xelatex.pdf')


# test compiling a figure to pdf with pdflatex
@switch_backend('pgf')
def test_pdflatex():
    if not check_for('pdflatex'):
        raise SkipTest('pdflatex + pgf is required')

    rc_pdflatex = {'font.family': 'serif',
                   'pgf.rcfonts': False,
                   'pgf.texsystem': 'pdflatex',
                   'pgf.preamble': [r'\usepackage[utf8x]{inputenc}',
                                    r'\usepackage[T1]{fontenc}']}
    mpl.rcParams.update(rc_pdflatex)
    create_figure()
    compare_figure('pgf_pdflatex.pdf')


# test updating the rc parameters for each figure
@switch_backend('pgf')
def test_rcupdate():
    if not check_for('xelatex') or not check_for('pdflatex'):
        raise SkipTest('xelatex and pdflatex + pgf required')

    rc_sets = []
    rc_sets.append({'font.family': 'sans-serif',
                    'font.size': 30,
                    'figure.subplot.left': .2,
                    'lines.markersize': 10,
                    'pgf.rcfonts': False,
                    'pgf.texsystem': 'xelatex'})
    rc_sets.append({'font.family': 'monospace',
                    'font.size': 10,
                    'figure.subplot.left': .1,
                    'lines.markersize': 20,
                    'pgf.rcfonts': False,
                    'pgf.texsystem': 'pdflatex',
                    'pgf.preamble': [r'\usepackage[utf8x]{inputenc}',
                                     r'\usepackage[T1]{fontenc}',
                                     r'\usepackage{sfmath}']})

    for i, rc_set in enumerate(rc_sets):
        mpl.rcParams.update(rc_set)
        create_figure()
        compare_figure('pgf_rcupdate%d.pdf' % (i+1))

if __name__ == '__main__':
    import nose
    nose.runmodule(argv=['-s','--with-doctest'], exit=False)
