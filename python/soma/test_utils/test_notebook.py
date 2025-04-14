import os
import re
import subprocess
import sys
import tempfile

try:
    import nbformat
    from jupyter_core.command import main as main_jupyter
except ImportError:
    print("cannot import nbformat and/or jupyter_core.command: cannot test notebooks")
    main_jupyter = None


def _notebook_run(path, output_nb, timeout=60):
    """Execute a notebook via nbconvert and collect output.
    :returns (parsed nb object, execution errors)

    from: https://www.christianmoscardi.com/blog/2016/01/20/jupyter-testing.html
    """
    if main_jupyter is None:
        print("cannot test notebook", path)
        return None, []

    dirname, __ = os.path.split(path)
    old_cwd = os.getcwd()
    os.chdir(dirname)
    if not os.path.isabs(path):
        path = os.path.basename(path)
    ret_code = 1
    args = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        f"--ExecutePreprocessor.timeout={timeout}",
        f"--ExecutePreprocessor.kernel_name=python{sys.version_info[0]}",
        "--output",
        output_nb,
        path,
    ]
    old_argv = sys.argv
    sys.argv = args
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])

    try:
        ret_code = main_jupyter()
    finally:
        sys.argv = old_argv
        os.chdir(old_cwd)

    return ret_code


def notebook_run(path, timeout=60):
    """Execute a notebook via nbconvert and collect output.
    :returns (parsed nb object, execution errors)

    from: https://www.christianmoscardi.com/blog/2016/01/20/jupyter-testing.html
    """
    if main_jupyter is None:
        print("cannot test notebook", path)
        return None, []

    dirname, __ = os.path.split(path)
    old_cwd = os.getcwd()
    os.chdir(dirname)
    nb = None
    fout = tempfile.mkstemp(suffix=".ipynb")
    os.close(fout[0])
    try:
        print("temp nb:", fout[1])
        args = [
            sys.executable,
            "-m",
            "soma.test_utils.test_notebook",
            path,
            fout[1],
            str(timeout),
        ]

        try:
            # call _notebook_run as an external process because it will
            # sys.exit()
            _ = subprocess.call(args)

            nb = nbformat.read(fout[1], nbformat.current_nbformat)
        except Exception as e:
            print("EXCEPTION:", e)
            return None, [e]
    finally:
        try:
            os.unlink(fout[1])
        except OSError:
            pass
        os.chdir(old_cwd)

    errors = [
        output
        for cell in nb.cells
        if "outputs" in cell
        for output in cell["outputs"]
        if output.output_type == "error"
    ]

    return nb, errors


def test_notebook(notebook_filename, timeout=60):
    """Almost the same as notebook_run() but returns a single arror code

    Parameters
    ----------
    notebook_filename: filename of the notebook (.ipynb) to test
    timeout: int
        max time in seconds to execute one cell

    Returns
    -------
    code: True if successful, False if failed
    """
    if main_jupyter is None:
        raise Warning(
            "cannot import nbformat and/or jupyter_core.command: cannot test notebooks"
        )

    print("running notebook test for", notebook_filename)
    nb, errors = notebook_run(notebook_filename, timeout)

    if len(errors) == 0:
        code = True
    else:
        code = False
    return code


if __name__ == "__main__":
    timeout = 60
    if len(sys.argv) >= 4:
        timeout = int(sys.argv[3])
    sys.exit(_notebook_run(sys.argv[1], sys.argv[2], timeout=timeout))
