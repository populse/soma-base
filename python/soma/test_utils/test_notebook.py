from __future__ import print_function
import os
import tempfile
import re
import sys
import subprocess
try:
    import nbformat
    from jupyter_core.command import main as main_jupyter
except ImportError:
    print('cannot import nbformat and/or jupyter_core.command: cannot test '
          'notebooks')
    main_jupyter = None


def _notebook_run(path, output_nb):
    """Execute a notebook via nbconvert and collect output.
       :returns (parsed nb object, execution errors)

       from: http://blog.thedataincubator.com/2016/06/testing-jupyter-notebooks/
    """
    if main_jupyter is None:
        print('cannot test notebook', path)
        return None, []

    dirname, __ = os.path.split(path)
    old_cwd = os.getcwd()
    os.chdir(dirname)
    ret_code = 1
    args = ["jupyter", "nbconvert", "--to", "notebook", "--execute",
      "--ExecutePreprocessor.timeout=60",
      "--ExecutePreprocessor.kernel_name=python%d" % sys.version_info[0],
      "--output", output_nb, path]
    old_argv = sys.argv
    sys.argv = args
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])

    try:
        ret_code = main_jupyter()
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)

    return ret_code


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
    nb = None
    with tempfile.NamedTemporaryFile(suffix=".ipynb") as fout:
        print('temp nb:', fout.name)
        args = [sys.executable, '-m', 'soma.test_utils.test_notebook',
                path, fout.name]

        try:
            # call _notebook_run as an external process because it will
            # sys.exit()
            ret_code = subprocess.call(args)

            fout.seek(0)
            nb = nbformat.read(fout, nbformat.current_nbformat)
        except Exception as e:
            print('EXCEPTION:', e)
            return None, [e]

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

    if len(errors) == 0:
        code = 0
    else:
        code = 1
    return code


if __name__ == '__main__':
    sys.exit(_notebook_run(sys.argv[1], sys.argv[2]))

