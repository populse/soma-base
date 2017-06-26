from __future__ import print_function
import os
import tempfile
import re
import sys
try:
    import nbformat
    from jupyter_core.command import main as main_jupyter
except ImportError:
    print('cannot import nbformat and/or jupyter_core.command: cannot test '
          'notebooks')
    main_jupyter = None


def notebook_run(path):
    """Execute a notebook via nbconvert and collect output.
       :returns (parsed nb object, execution errors)

       from: http://blog.thedataincubator.com/2016/06/testing-jupyter-notebooks/
    """
    if main_jupyter is None:
        print('cannot test notebook', path)
        return None, []

    dirname, __ = os.path.split(path)
    os.chdir(dirname)
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
        args = ["jupyter", "nbconvert", "--to", "notebook", "--execute",
          "--ExecutePreprocessor.timeout=60",
          "--ExecutePreprocessor.kernel_name=python%d" % sys.version_info[0],
          "--output", fout.name, path]
        try:
            old_argv = sys.argv
            sys.argv = args
            sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

            try:
                ret_code = main_jupyter()

                fout.seek(0)
                nb = nbformat.read(fout, nbformat.current_nbformat)
            except Exception as e:
                return None, [e]
        finally:
            sys.argv = old_argv

    errors = [output for cell in nb.cells if "outputs" in cell
                     for output in cell["outputs"]\
                     if output.output_type == "error"]

    return nb, errors


def test_notebook(notebook_filename):
    """Almost the same as notebook_run() but returns a single arror code

    Parameters
    ----------
    notebook_filename: filename of the notebook (.ipynb) to test

    Returns
    -------
    code: 0 if successful, 1 if failed
    """
    print("running notebook test for", notebook_filename)
    nb, errors = notebook_run(notebook_filename)
    print('*********** DONE *************')

    if len(errors) == 0:
        code = 0
    else:
        code = 1
    return code

