"""
Run worker functions in separate processes.

The use case is somewhat similar to what can be done using either :class:`queue.Queue <Queue.Queue>` and threads, or using :mod:`multiprocessing`. That is: run a number of independent job functions, dispatched over a number of worker threads/processes.

The mpfork module is useful in cases the above methods cannot work:

* threading in python is globally mainly inefficient because of the GIL.
* :mod:`multiprocessing` makes heavy use of pickles to pass objects and parameters, and there are cases we are using objects which cannot be pickled, or which pickling generates heavy IO traffic (large data objects)

The method here is based on the queue / thread schema, but uses fork() to actually execute the workers in a separate process. Only results are passed through pickles, so the worker return results must be picklable, but not the input arguments and objects.

Use:

* allocate a :class:`Queue <Queue.Queue>`
* allocate a results list with the exact size of the jobs number
* allocate a set of worker threads (typically one per processor or core). The function :func:`allocate_workers` can do this for you.
* fill the queue with jobs, each being a tuple (job_index, function, args, kwargs, results_list)
* add a number of empty jobs (None) to the queue, one per allocated worker: this will be the marker for the end of processing in each worker thread. It is necessary to explicitly add these empty jobs since an empty queue is not the signal for the end of processing: it can be re-filled at any time.
* jobs run in workers
* join the queue
* join the worker threads
* the result list gets the return data for each job

::

    njobs = 10
    q = queue.Queue()
    res = [None] * njobs
    workers = allocate_workers(q, 0) # one per core
    for i in range(njobs):
        job = (i, sum, ((i, i), ), {}, res)
        q.put(job)

    # add as many empty jobs as the workers number to end them
    for i in range(len(workers)):
        q.put(None)

    # wait for every job to complete
    q.join()
    # terminate all threads
    for w in workers:
        w.join()

    print('result:', res)

In case of error, the job result will be an exception with stack information: (exception type, exception instance, stack_info)


Availability: Unix
"""

import multiprocessing
import os
import sys
import tempfile
import threading

try:
    import cpickle as pickle
except ImportError:
    import pickle


def run_job(f, *args, **kwargs):
    """Internal function, runs the function in a remote process.
    Uses fork() to perform it.

    Availability: Unix
    """
    out_file = tempfile.mkstemp()
    os.close(out_file[0])
    pid = os.fork()
    if pid != 0:
        # parent: wait for the child
        pid, status = os.waitpid(pid, 0)
        # read output file
        # print('read from', os.getpid(), ':', out_file[1])
        if os.stat(out_file[1]).st_size == 0:
            # child did not write anything
            os.unlink(out_file[1])
            raise OSError("child did not output anything")
        if status != 0:
            os.unlink(out_file[1])
            raise RuntimeError(f"subprocess error: {status}")
        result = pickle.load(open(out_file[1], "rb"))
        os.unlink(out_file[1])
        # traceback objects cannot be pickled...
        # if isinstance(result, tuple) and len(result) == 3 \
        # and isinstance(result[1], Exception):
        ## result is an axception with call stack: reraise it
        # raise result[0], result[1], result[2]
        if isinstance(result, Exception):
            raise result
        return result

    # child process
    try:
        try:
            # print('exec in', os.getpid(), ':', f, args, kwargs)
            result = f(*args, **kwargs)
            # print('OK')
        except Exception as e:
            # traceback objects cannot be pickled...
            # result = (type(e), e, sys.exc_info()[2])
            result = e
        # print('write:', out_file[1], ':', result)
        try:
            pickle.dump(result, open(out_file[1], "wb"), protocol=2)
        except Exception as e:
            print("pickle failed:", e, "\nfor object:", type(result))
    finally:
        # sys.exit() is not enough
        os._exit(0)


def worker(q, thread_only, *args, **kwargs):
    """Internal function: worker thread loop:
    * pick a job in the queue q
    * execute it, either in the current thread, or in a remote process (using
      run_job()), depending on the thread_only parameter value
    * store the result in the result list
    * start again with another job

    The loop ends when a job in the queue is None.

    .. warning::
        Here we are making use of fork() (Unix only) inside a thread. Some systems do not behave well in this situation.
        See :func:`the os.fork() doc <os.fork>`
    """
    while True:
        item = q.get()
        if item is None:
            q.task_done()
            break
        try:
            # print('run item in', os.getpid(), ':', item[:-1])
            sys.stdout.flush()
            i, f, argsi, kwargsi, res = item
            argsi = argsi + args
            kwargs = dict(kwargs)
            kwargs.update(kwargsi)
            try:
                if thread_only:
                    try:
                        result = f(*argsi, **kwargs)
                    except Exception as e:
                        result = e
                else:
                    result = run_job(f, *argsi, **kwargs)
                # print('result:', i, result)
                res[i] = result
            except Exception as e:
                res[i] = (type(e), e, sys.exc_info()[2])
                print(e)
        finally:
            # print('task done in', os.getpid(), ':', i, f)
            q.task_done()
            sys.stdout.flush()


def allocate_workers(q, nworker=0, thread_only=False, *args, **kwargs):
    """Utility function to allocate worker threads.

    Parameters
    ----------
    q: :class:`Queue <Queue.Queue>` instance
        the jobs queue which will be fed with jobs for processing
    thread_only: bool
        if True, workers will run jobs in the worker thread, not using a
        separate process. This flag thus allows to choose a threaded or
        multiprocessing implementation.
    nworker: int
        number of worker threads (jobs which will run in parallel). A positive
        number (1, 2...) will be used as is, 0 means all available CPU cores
        (see :func:`multiprocessing.cpu_count`), and a negative number means
        all CPU cores except this given number.
    args, kwargs:
        additional arguments will be passed to the jobs function(s) after
        individual jobs arguments: they are args common to all jobs (if any)

    Returns
    -------
    workers: list
        workers list, each is a :class:`thread <threading.Thread>` instance
        running the worker loop function. Threads are already started (ie.
    """
    if nworker == 0:
        nworker = multiprocessing.cpu_count()
    elif nworker < 0:
        nworker = multiprocessing.cpu_count() + nworker
        if nworker < 1:
            nworker = 1
    workers = []
    for i in range(nworker):
        w = threading.Thread(target=worker, args=(q, thread_only) + args, kwargs=kwargs)
        w.start()
        workers.append(w)
    return workers
