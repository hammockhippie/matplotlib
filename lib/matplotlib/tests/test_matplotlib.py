import os
import subprocess
import sys

import pytest

import matplotlib


@pytest.mark.skipif(
    os.name == "nt", reason="chmod() doesn't work as is on Windows")
@pytest.mark.skipif(os.name != "nt" and os.geteuid() == 0,
                    reason="chmod() doesn't work as root")
def test_tmpconfigdir_warning(tmpdir):
    """Test that a warning is emitted if a temporary configdir must be used."""
    mode = os.stat(tmpdir).st_mode
    try:
        os.chmod(tmpdir, 0)
        proc = subprocess.run(
            [sys.executable, "-c", "import matplotlib"],
            env={**os.environ, "MPLCONFIGDIR": str(tmpdir)},
            stderr=subprocess.PIPE, universal_newlines=True, check=True)
        assert "set the MPLCONFIGDIR" in proc.stderr
    finally:
        os.chmod(tmpdir, mode)


def test_use_doc_standard_backends():
    """
    Test that the standard backends mentioned in the docstring of
    matplotlib.use() are the same as in matplotlib.rcsetup.
    """
    def parse(key):
        backends = []
        for line in matplotlib.use.__doc__.split(key)[1].split('\n'):
            if not line.strip():
                break
            backends += [e.strip() for e in line.split(',') if e]
        return backends

    assert (set(parse('- interactive backends:\n')) ==
            set(matplotlib.rcsetup.interactive_bk))
    assert (set(parse('- non-interactive backends:\n')) ==
            set(matplotlib.rcsetup.non_interactive_bk))


def test_importable_with__OO():
    """
    When using -OO or export PYTHONOPTIMIZE=2, docstrings are discarded,
    this simple test may prevent something like issue #17970.
    """
    program = (
        "import numpy as np; "
        "import numpy.ma as ma; "
        "import matplotlib as mpl; "
        "import matplotlib.pyplot as plt; "
        "import matplotlib.cbook as cbook; "
        "import matplotlib.patches as mpatches"
    )
    cmd = [sys.executable, '-OO', '-c', program]
    assert subprocess.call(cmd) == 0
