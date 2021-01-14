"""
ThreadPool implements pool of threads with the method 'map' that applies
given function for each element of the list passed.

Example:

    thread_pool = ThreadPool(10)
    result = thread_pool.map(lambda x: x**2, [1, 2, 3])

    print(result)  # [1, 4, 9]
"""

import threading
from queue import Queue, Empty


class ThreadPool:
    def __init__(self, threads_num):
        self._threads_num = threads_num

    def map(self, func, lst):
        """
        Applies 'func' to each element in 'lst'. The result is a list. If
        an error occurred, None will be stored in the result.
        """
        # Input queue (elements and their indices)
        queue = Queue()
        for i, e in enumerate(lst):
            queue.put((i, e))

        # Queue for the result
        result_queue = Queue()

        # Lock to modify result_queue
        lock = threading.Lock()

        # Target function for a thread
        def target(queue, result_queue, lock):
            while True:
                # Get next element from queue, break if empty
                try:
                    idx, x = queue.get(block=False)
                except Empty:
                    break
                else:
                    # Call 'func', if an error set y to None
                    try:
                        y = func(x)
                    except:
                        y = None

                    # Fill result_queue
                    with lock:
                        result_queue.put((idx, y))

        # Create and execute threads
        threads = [
            threading.Thread(target=target, args=(queue, result_queue, lock))
            for _ in range(self._threads_num)
        ]
        list(map(threading.Thread.start, threads))
        list(map(threading.Thread.join, threads))

        # Fill result list from result_queue
        result = [None] * len(lst)
        while not result_queue.empty():
            idx, y = result_queue.get()
            result[idx] = y

        return result
