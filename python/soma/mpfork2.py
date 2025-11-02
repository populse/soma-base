# -*- coding: utf-8 -*-

'''
Run worker functions in separate processes.

The use case is somewhat similar to what can be done using either :class:`queue.Queue <Queue.Queue>` and threads, or using :mod:`multiprocessing`. That is: run a number of independent job functions, dispatched over a number of worker threads/processes.

The mpfork and mpfork2 modules are useful in cases the above methods cannot work:

* threading in python is globally mainly inefficient because of the GIL.
* :mod:`multiprocessing` makes heavy use of pickles to pass objects and parameters, and there are cases we are using objects which cannot be pickled, or which pickling generates heavy IO traffic (large data objects)

mpfork and mpfork2

The method here is based on the queue / thread schema, but uses fork() to actually execute the workers in a separate process. Only results are passed through pickles, so the worker return results must be picklable, but not the input arguments and objects.

* mpfork forks from a worker thread. This is the most efficient, but fork and thread are not easily mixable: only the current thread is left running in the forked process, all other ones are stopped. However locks left in other threads may block the entire process. In such cases, or if the main thread is running graphical objects and an event loop (like Qt), expect mpfork to lock.
In such a case, please consider using mpfork2 instead.

* mpfork2 forks from the main thread, earlier than mpfork (basically then workers are instantiated), which make it more stable. Compared to mpfork, workers need to be manually started using Worker.start(), and jobs input data need to be transfered via pickles. Hoxever large data may be stored in the calling object before forking.

* in case workers need to perform graphical or GPU renderings, the fork mode of mpfork2 will also not be sufficient, because event loops often need threads and locks, and because graphical resources will not be duplicated and allocated in the forked process. In this situation, mpfork2 offers a "spawn" mode, which doesn't use fork() (and thus might workk on non-unix systems). Here, a new process has to be started, and initialized in the worker process before jobs can be run. This is done by passing `fork_mode="spawn"` to allocate_workers(), and also passing an init function and parameters, using `init_child_function=(function, args, kwargs)`. The function and args need to be picklable.

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
    workers = allocate_workers(q, res, 0) # one per core
    for i in range(njobs):
        job = (i, sum, ((i, i), ), {})
        q.put(job)

    # add as many empty jobs as the workers number to end them
    for i in range(len(workers)):
        q.put(None)

    # start all workers
    for w in workers:
        w.start()

    # wait for every job to complete
    q.join()

    # terminate all workers
    for w in workers:
        w.join()

    print('result:', res)


In case of error, the job result will be an exception with stack information: (exception type, exception instance, stack_info)


Availability: Unix
'''

import multiprocessing
import threading
import os
import tempfile
import sys
import subprocess
import shutil
try:
    import cpickle as pickle
except ImportError:
    import pickle


_gpu_start_commands = None


class Worker:
    def __init__(self, queue, result, args=[], kwargs={}, spawn_prefix=None):
        self.queue = queue
        self.args = args
        self.kwargs = dict(kwargs)
        self.pid = None
        self.spawn_prefix = []
        self.result = result
        if 'fifo' in kwargs:
            self.fifo = kwargs['fifo']
            del self.kwargs['fifo']
        else:
            fifo = tempfile.mkstemp()
            os.close(fifo[0])
            os.unlink(fifo[1])
            os.mkfifo(fifo[1])
            self.fifo = fifo[1]
        if 'exchange_file' in kwargs:
            self.exchange_file = kwargs['exchange_file']
            del self.kwargs['exchange_file']
        else:
            exchange_file = tempfile.mkstemp()
            os.close(exchange_file[0])
            self.exchange_file = exchange_file[1]
        self.thread = None
        self.init_child_function = ()
        self.fork_mode = 'fork'
        if 'init_child_function' in kwargs:
            self.init_child_function = kwargs['init_child_function']
            del self.kwargs['init_child_function']
        if 'fork_mode' in kwargs:
            self.fork_mode = kwargs['fork_mode']
            del self.kwargs['fork_mode']
            if self.fork_mode == 'spawn' and spawn_prefix is not None:
                self.spawn_prefix = spawn_prefix

    def fork(self):
        if self.fork_mode == 'fork':
            # print('forking')
            # sys.stdout.flush()
            self.pid = os.fork()
            # print('forked pid:', self.pid)
            # sys.stdout.flush()
            if self.pid != 0:
                # parent: return the main program
                pass
            else:
                # child: process incoming jobs
                self.child_loop()
        elif self.fork_mode == 'spawn':
            d = {
                'args': self.args,
                'kwargs': self.kwargs,
                'fifo': self.fifo,
                'exchange_file': self.exchange_file,
                'init_child_function': self.init_child_function,
                'fork_mode': self.fork_mode,
            }
            with open(self.exchange_file, 'wb') as f:
                pickle.dump(d, f)
            cmd = self.spawn_prefix + [sys.executable, '-m', 'soma.mpfork2',
                                       'worker', self.exchange_file]
            # print('spawn command:', cmd)
            self.subproc = subprocess.Popen(cmd)

    def start(self):
        self.thread = threading.Thread(target=self.parent_loop)
        self.thread.start()

    def join(self):
        self.thread.join()

    def parent_loop(self):
        ''' Internal function: worker thread loop:
        * pick a job in the queue q
        * execute it, either in the current thread, or in a remote process
          (using run_job()), depending on the thread_only parameter value
        * store the result in the result list
        * start again with another job

        The loop ends when a job in the queue is None.

        .. warning::
            Here we are making use of fork() (Unix only) inside a thread. Some systems do not behave well in this situation.
            See :func:`the os.fork() doc <os.fork>`
        '''
        # print('parent_loop')
        # sys.stdout.flush()

        # in spawn mode, wait for the worker to be ready
        if self.fork_mode == 'spawn':
            # print('waiting for child to be ready...')
            # sys.stdout.flush()
            with open(self.fifo) as f:
                line = f.readline()
            if line != 'ready.\n':
                raise ValueError('Worker did not answer the expected message')
            # print('child is ready, proceeding with jobs.')
            # sys.stdout.flush()

        q = self.queue
        while True:
            item = q.get()
            if item is None:
                self.run_job(None)  # send end of worker to the child
                q.task_done()
                break
            try:
                # print('run item in', os.getpid(), ':', item[:-1])
                # sys.stdout.flush()
                i, f, argsi, kwargsi = item
                try:
                    result = self.run_job(f, *argsi, **kwargsi)
                    # print('result:', i, result)
                    # sys.stdout.flush()
                    self.result[i] = result
                except Exception as e:
                    # print('EXCEPTION IN PARENT:', e)
                    self.result[i] = (type(e), e, sys.exc_info()[2])
                    # print(e)
                    # sys.stdout.flush()
            finally:
                # print('task done in', os.getpid(), ':', i, f)
                # sys.stdout.flush()
                q.task_done()
                sys.stdout.flush()

        if self.fork_mode == 'fork':
            pid, status = os.waitpid(self.pid, 0)
        else:
            status = self.subproc.wait()
        self.pid = None
        os.unlink(self.fifo)
        self.fifo = None
        os.unlink(self.exchange_file)
        self.exchange_file = None

    def child_loop(self):
        # we are in the main (single) thread of the child process
        # child process
        # print('child_loop')
        # sys.stdout.flush()

        # in spawn mode, send a "ready" message to the parent
        if self.fork_mode == 'spawn':
            # print('sending ready message to my parent.')
            # sys.stdout.flush()
            with open(self.fifo, 'w') as f:
                f.write('ready.\n')

        # print('init func:', self.init_child_function)
        # sys.stdout.flush()
        if self.init_child_function:
            init_func = self.init_child_function[0]
            args = ()
            kwargs = {}
            if len(self.init_child_function) >= 2:
                args = self.init_child_function[1]
                if len(self.init_child_function) >= 3:
                    kwargs = self.init_child_function[2]
            # print('calling:', init_func)
            # print('args:', args)
            # print('kwargs:', kwargs)
            # sys.stdout.flush()
            init_func(*args, **kwargs)

        try:
            while True:
                # print('waiting for job')
                # sys.stdout.flush()
                try:
                    with open(self.fifo, 'r') as f:
                        # print('reading fifo')
                        # sys.stdout.flush()
                        cmd = f.readline()
                        # print('cmd read from child:', cmd)
                        # sys.stdout.flush()
                    if cmd != 'job sent.\n':
                        print('ERROR')
                        sys.stdout.flush()
                    with open(self.exchange_file, 'rb') as f:
                        job = pickle.load(f)
                except Exception as e:
                    print('read exception:', e)
                    sys.stdout.flush()
                    raise
                # print('job read done:', job)
                # sys.stdout.flush()
                function = job['function']
                args = job['args']
                kwargs = job['kwargs']
                # print('exec in', os.getpid(), ':', function, args, kwargs)
                # print('args:', self.args)
                # print('kwargs:', self.kwargs)
                # sys.stdout.flush()
                self_args = self.args
                if function is None:
                    break  # stop child
                try:
                    if isinstance(function, str):
                        # assume it is a name inside the 1st arg "self"
                        function = getattr(self.args[0], function)
                        self_args = self.args[1:]
                    job_args = list(self_args) + list(args)
                    job_kwargs = dict(self.kwargs)
                    job_kwargs.update(kwargs)
                    result = function(*job_args, **job_kwargs)
                    # print('OK')
                    # sys.stdout.flush()
                except Exception as e:
                    # traceback objects cannot be pickled...
                    #result = (type(e), e, sys.exc_info()[2])
                    # print('except in child execution:', e)
                    # sys.stdout.flush()
                    # import traceback
                    # traceback.print_exc()
                    result = e
                # print('write:', self.fifo, ':', result)
                # sys.stdout.flush()
                with open(self.exchange_file, 'wb') as f:
                    pickle.dump(result, f)
                with open(self.fifo, 'w') as f:
                    f.write('result sent.\n')
                    f.flush()
                # print('child has sent the answer.')
                # sys.stdout.flush()
        finally:
            # # sys.exit() is not enough
            # print('exiting child process', os.getpid())
            # sys.stdout.flush()
            os._exit(0)
        pass

    def run_job(self, function, *args, **kwargs):
        ''' Internal function, runs the function in the remote process.
        '''
        # print('run_job for', self.pid)
        # sys.stdout.flush()
        job = {'function': function, 'args': args, 'kwargs': kwargs}
        try:
            with open(self.exchange_file, 'wb') as f:
                # print('writing pickle')
                # sys.stdout.flush()
                pickle.dump(job, f)
        except Exception as e:
            print('Pickling EXC while writing file:', self.exchange_file,
                  ':', e)
            sys.stdout.flush()
        # print('pickle written.')
        # sys.stdout.flush()
        with open(self.fifo, 'w') as f:
            # print('writing fifo for', self.pid)
            # sys.stdout.flush()
            f.write('job sent.\n')
            f.flush()
            # print('   dumped.')
            # sys.stdout.flush()
        # print('pickle sent')
        # sys.stdout.flush()

        if function is None:
            # end of worker
            return

        # wait for end of execution and read output
        # print('read from', os.getpid(), ':', self.fifo)
        # sys.stdout.flush()
        with open(self.fifo, 'r') as f:
            answer = f.readline()
            # print('answer:', answer)
            # sys.stdout.flush()
        if answer != 'result sent.\n':
            print('ERROR!')
            sys.stdout.flush()
        with open(self.exchange_file, 'rb') as f:
            result = pickle.load(f)
            # print('result read.')
            # sys.stdout.flush()

        # traceback objects cannot be pickled...
        #if isinstance(result, tuple) and len(result) == 3 \
                #and isinstance(result[1], Exception):
            ## result is an axception with call stack: reraise it
            #raise result[0], result[1], result[2]
        if isinstance(result, Exception):
            raise result
        return result


def allocate_workers(q, result, nworker=0, max_workers=0, *args, **kwargs):
    ''' Utility function to allocate worker threads.

    Parameters
    ----------
    q: :class:`Queue <Queue.Queue>` instance
        the jobs queue which will be fed with jobs for processing
    result: list
        Modifiable list, each job will insert its result in it. The list size
        must be allocated before workers are started.
    nworker: int
        number of worker threads (jobs which will run in parallel). A positive
        number (1, 2...) will be used as is, 0 means all available CPU cores
        (see :func:`multiprocessing.cpu_count`), and a negative number means
        all CPU cores except this given number.
    max_workers: int
        max number of workers: if nworker is 0, the number of CPU cores is
        used,
        but might exceed the number of actual jobs to be done. To limit this,
        you can use the number of jobs (if known) here. 0 means no limit.
    spawn_prefixes: list
        If run in spawn mode, the commandline of the spawn process can each get
        a launcher prefix. Typically used to switch to a given GPU using
        "switcherooctl". It may be a list of lists, each for a given worker,
        like: [["switcherooctl", "-g", "0"], ["switcherooctl", "-g", "1"]],
        or a single list, where "%(WORKER_ID)s" will be replaced with the index
        of the worker. You may use the function
        `select_gpu_prefix_for_workers()` to help this.
    init_child_function: list or tuple
        in "spawn" fork_mode, an init function will be called in the child
        worker process in order to make it in the right state to process jobs.
        The init funciton is specified here, as a list or tuple [function,
        args, kwargs], with args being a tuple and kwargs a parameters dict.
        args and kwargs are optional if the function does not need them.
    args, kwargs:
        additional arguments will be passed to the job function(s) after
        individual jobs arguments: they are args common to all jobs (if any)

    Returns
    -------
    workers: list
        workers list, each is a :class:`Worker` instance
        running the worker loop function. Threads are already started (ie.
    '''
    spawn_prefixes = []
    if 'spawn_prefixes' in kwargs:
        spawn_prefixes = kwargs['spawn_prefixes']
        kwargs = dict(kwargs)
        del kwargs['spawn_prefixes']
    if nworker == 0:
        nworker = multiprocessing.cpu_count()
    elif nworker < 0:
        nworker = multiprocessing.cpu_count() + nworker
        if nworker < 1:
            nworker = 1
    if max_workers > 0 and nworker > max_workers:
        nworker = max_workers
    workers = []
    for i in range(nworker):
        spawn_prefix = []
        if spawn_prefixes:
            if isinstance(spawn_prefixes, list):
                spawn_prefix = spawn_prefixes[i % len(spawn_prefixes)]
            else:
                spawn_prefix = spawn_prefixes
            spawn_prefix = [x % {'WORKER_ID': i} for x in spawn_prefix]
        # print('spawn_prefix for worker', i, ':', spawn_prefix)
        w = Worker(queue=q, result=result, args=args, kwargs=kwargs,
                   spawn_prefix=spawn_prefix)
        w.fork()
        workers.append(w)
    return workers


def gpu_start_prefixes():
    ''' Helper function used by `select_gpu_prefix_for_workers()`

    It uses the `switcherooctl` tool, if available, to build a list of available GPUs and command to start a process for it.

    Returns
    -------
    gpu_start_commands: dict
        {gpu_num: [command prefix to start]}
    '''
    global _gpu_start_commands
    if _gpu_start_commands is None:
        gpu_list = {}
        if shutil.which('switcherooctl') is not None:
            dev_list = subprocess.check_output(['switcherooctl', 'list'])
            dev_list = dev_list.decode().split('\n')
            for line in dev_list:
                if line.startswith('Device:'):
                    gpu = int(line.split(' ')[1])
                    gpu_list[gpu] = ['switcherooctl', 'launch', '-g', str(gpu)]
        _gpu_start_commands = gpu_list
    return _gpu_start_commands


def select_gpu_prefix_for_workers(gpu_workers=0, max_workers=0):
    ''' Command prefixes for each worker for using multiple GPUs.

    This function is useful to run workers for the mpfork2 module which will
    run several GPUs. Its result may be passed to the `spawn_prefixes`
    parameter of the `allocate_workers()` function, when several GPUs are
    present on the system, like a multi-GPU machine, or a laptop with both an
    integrated GPU and a more powerful one using Optimus.

    Parameters
    ----------
    gpu_workers: int or dict
        specify GPU worker limits. If it is a single number, it is used as a
        global number and is adjusted by the CPU core count (not GPU) if
        negative or nul. GPU workers will be dispateched at equal numbers.
        If it is a dict, then each GPU can be assigned a limit of instances,
        ex: `{1: 2, 0: 3, 2: 0}` means at most 2 workers for GPU 1, 3 workers
        for GPU 0, and the remaining numbers of CPU cores for GPU 2. Note that
        the order might be important as the first appearing in the list will be
        used first, so at higher priority.
    max_workers: int
        max number of expected jobs: limits the overall number of workers. 0
        means no jobs limit: use all available CPU cores.

    Returns
    -------
    prefixes: list of list
        For each expected worker, a start command prefix based on the
        `switcherooctl` tool, like:
        [["switcherooctl", "launch", "-g", "0"],
        ["switcherooctl", "launch", "-g", "1"]] etc.
    '''
    import numpy as np

    nworker = gpu_workers
    gpu_list = gpu_start_prefixes()
    gpu_prefixes = {}
    if isinstance(nworker, int):
        if nworker == 0:
            nworker = multiprocessing.cpu_count()
        elif nworker < 0:
            nworker = multiprocessing.cpu_count() + nworker
            if nworker < 1:
                nworker = 1
        if max_workers > 0 and nworker > max_workers:
            nworker = max_workers
        if not gpu_list:
            gpu_prefixes = {0:  [[]] * nworker}
        else:
            gl = list(gpu_list.keys())
            gl = gl[1:2] + [gl[0]] + gl[1:]  # set GPU 0 at position 1
            n = nworker // len(gpu_list)
            nx = nworker % len(gpu_list)
            for i, g in enumerate(gl):
                ng = n
                if i < nx:
                    ng += 1
                cmd = gpu_list[g]
                gpu_prefixes[g] = [cmd] * ng
    else:  # workers by gpu
        ncpu = multiprocessing.cpu_count()
        if max_workers > 0:
            ncpu = min((multiprocessing.cpu_count(), max_workers))
        if gpu_list:
            nworker = {k: v for k, v in nworker.items() if k in gpu_list}
        taken = 0
        gmax = {}
        for g, n in nworker.items():
            if n > 0:
                gmax[g] = n
                taken += n
            else:
                gmax[g] = ncpu + n
                taken += ncpu + n
        taken = sum(gmax.values())
        gk = list(gmax.keys())
        while taken > ncpu:
            i = np.argmax(list(gmax.values()))
            gmax[gk[i]] -= 1
            taken -= 1
        if gpu_list:
            gpu_prefixes = {g: [gpu_list[g]] * n for g, n in gmax.items()}
        else:
            gpu_prefixes = {g: [[]] * n for g, n in gmax.items()}

    prefixes = []
    keys = list(gpu_prefixes.keys())
    index = 0
    while gpu_prefixes:
        gl = gpu_prefixes[keys[index]]
        cmd = gl.pop(0)
        prefixes.append(cmd)
        if len(gl) == 0:
            del gpu_prefixes[keys[index]]
            del keys[index]
        else:
            index += 1
        if index >= len(keys):
            index = 0

    return prefixes


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != 'worker':
        print('Commandline mode for soma.mpfork2: run a worker. This mode '
              'should be used only by the internal mechanism of Worker in '
              'spawn mode.')
        print(f'usage: {sys.executable} -m soma.mpfork2 <exchange_file>')
        print('read pickled parameters dict from the exchange file and starts '
              'the worker loop.')
        sys.exit(1)

    exchange_file = sys.argv[2]
    with open(exchange_file, 'rb') as f:
        d = pickle.load(f)
    kwargs = d.get('kwargs', {})
    for k in ('fifo', 'exchange_file', 'init_child_function', 'fork_mode'):
        if k in d:
            v = d[k]
            kwargs[k] = v

    worker = Worker(None, None, args=d.get('args', []), kwargs=kwargs)
    worker.child_loop()
