import math
import queue
import sys
import unittest

from soma import mpfork


class TestMPFork(unittest.TestCase):
    if not sys.platform.startswith("win"):

        def test_mpfork(self):
            njobs = 10
            q = queue.Queue()
            res = [None] * njobs
            workers = mpfork.allocate_workers(q, 4)
            self.assertEqual(len(workers), 4)
            for i in range(njobs):
                job = (i, sum, ((i, i),), {}, res)
                q.put(job)

            # add as many empty jobs as the workers number to end them
            for i in range(len(workers)):
                q.put(None)

            # wait for every job to complete
            q.join()
            # terminate all threads
            for w in workers:
                w.join()

            self.assertEqual(res, [i * 2 for i in range(njobs)])

        def test_mpfork_with_exception1(self):
            njobs = 10
            q = queue.Queue()
            res = [None] * njobs
            workers = mpfork.allocate_workers(q, -10)
            self.assertTrue(len(workers) >= 1)
            for i in range(njobs):
                job = (i, math.sqrt, (i - 2,), {}, res)
                q.put(job)

            # add as many empty jobs as the workers number to end them
            for i in range(len(workers)):
                q.put(None)

            # wait for every job to complete
            q.join()
            # terminate all threads
            for w in workers:
                w.join()

            self.assertTrue(isinstance(res[0], tuple))
            self.assertTrue(res[0][0] is ValueError)
            self.assertTrue(isinstance(res[1], tuple))
            self.assertTrue(res[1][0] is ValueError)
            self.assertEqual(res[2:], [math.sqrt(i) for i in range(njobs - 2)])

        def test_mpfork_with_exception2(self):
            njobs = 10
            q = queue.Queue()
            res = [None] * njobs
            workers = mpfork.allocate_workers(q, 0)
            self.assertTrue(len(workers) >= 1)

            def job_func1(x):
                if x >= 2:
                    return x
                sys.exit(int(x))

            for i in range(njobs):
                job = (i, job_func1, (i,), {}, res)
                q.put(job)

            # add as many empty jobs as the workers number to end them
            for i in range(len(workers)):
                q.put(None)

            # wait for every job to complete
            q.join()
            # terminate all threads
            for w in workers:
                w.join()

            # print(res, file=sys.stderr)
            self.assertTrue(isinstance(res[0], tuple))
            self.assertTrue(res[0][0] is OSError)
            self.assertTrue(isinstance(res[1], tuple))
            self.assertTrue(res[1][0] is OSError)
            self.assertEqual(res[2:], [i + 2 for i in range(njobs - 2)])


def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMPFork)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
