import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from matplotlib.testing import subprocess_run_for_testing

nbformat = pytest.importorskip('nbformat')
pytest.importorskip('nbconvert')
pytest.importorskip('ipykernel')

# From https://blog.thedataincubator.com/2016/06/testing-jupyter-notebooks/


def test_ipynb():
    nb_path = Path(__file__).parent / 'test_nbagg_01.ipynb'

    with TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir, "out.ipynb")
        subprocess_run_for_testing(
            ["jupyter", "nbconvert", "--to", "notebook",
             "--execute", "--ExecutePreprocessor.timeout=500",
             "--output", str(out_path), str(nb_path)],
            env={**os.environ, "IPYTHONDIR": tmpdir},
            check=True)
        with out_path.open() as out:
            nb = nbformat.read(out, nbformat.current_nbformat)

    errors = [output for cell in nb.cells for output in cell.get("outputs", [])
              if output.output_type == "error"]
    assert not errors
