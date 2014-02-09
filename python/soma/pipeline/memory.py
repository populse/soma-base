# python system modules
import os
import shutil
import string

# spm copy tools
from soma.pipeline.spm_memory_utils import local_map, last_timestamp
from soma.utils import ensure_is_dir

# joblib caching
from joblib import Memory


def _run_process(subj_output_dir, description, process_instance):
    """ Execute the process
    """
    return process_instance()


def _joblib_run_process(subj_output_dir, description, process_instance):
    """ Use joblib smart-caching.
    Deal with files and SPM nipype processes.
    Do not check if files have been deleted by any users or scripts
    """
    # smart-caching directory
    cleanup_table = string.maketrans('()\\/:*?"<>| \t\r\n\0',
                                     '________________')
    name = description.lower().translate(cleanup_table)
    subj_output_dir = os.path.join(subj_output_dir, name)
    ensure_is_dir(subj_output_dir)

    # init smart-caching with joblib
    mem = Memory(cachedir=subj_output_dir, verbose=2)

    # copy : bool : copy all files (used when image headers are modified)
    copy = False
    if process_instance.id.startswith("nipype.interfaces.spm"):
        copy = True

    # first get input file modified times
    inputs = {}
    for name, trait in process_instance.user_traits().iteritems():
        if not trait.output:
            inputs[name] = process_instance.get_parameter(name)

    last_modified_file = last_timestamp(inputs)

    #if copy:
        # update function arguments : Symbolic links
    #    local_inputs = local_map(inputs, subj_output_dir, False)
    #else:
    #    local_inputs = inputs.copy()

    # interface smart-caching with joblib
    _mprocess = mem.cache(process_instance.__call__)

    # find and update joblib smart-caching directory
    output_dir, argument_hash = _mprocess.get_output_dir()
    if os.path.exists(output_dir):
        cache_time = os.path.getmtime(output_dir)
        # call the joblib clear function if necessary to deal with
        # files on disk
        if cache_time < last_modified_file:
            _mprocess.clear()
    else:
        # restrain joblib to one directory to handle output files on disk
        to_remove = [os.path.join(_mprocess._get_func_dir(), x)
            for x in os.listdir(_mprocess._get_func_dir())
            if os.path.isdir(os.path.join(_mprocess._get_func_dir(), x))]
        for joblib_folder in to_remove:
            shutil.rmtree(joblib_folder)

    # clean the output directory and copy the input files if requested
    is_memorized = (_mprocess._check_previous_func_code(stacklevel=3) and
                    os.path.exists(output_dir))
    if copy and not is_memorized:
        to_delete = [os.path.join(subj_output_dir, x)
                     for x in os.listdir(subj_output_dir)]
        for item in to_delete:
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
        local_map(inputs, subj_output_dir, True)

    # call interface
    outputs = _mprocess()

    # remove symbolic links
    to_delete = [os.path.join(subj_output_dir, x)
                  for x in os.listdir(subj_output_dir)
                  if os.path.islink(os.path.join(subj_output_dir, x))]
    for item in to_delete:
        os.unlink(item)

    # return the output interface information
    return outputs