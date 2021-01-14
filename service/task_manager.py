"""
There are abstract classes for tasks and task manager implementation that
run registered tasks in its own processes (using multiprocessing).

Example:

    task_manager = TaskManager()

    @task_manager.register
    class TestTask(PeriodicTask):
        timeout = 1.0

        def handle(self):
            print("test")

    task_manager.run()
"""

import logging
from time import sleep

import multiprocessing as mp


class BaseTask:
    """
    Base class for tasks. It requires method 'run' to implement.
    """

    def run(self):
        """
        Runs the task. Must be implements.
        """
        raise NotImplementedError()


class PeriodicTask(BaseTask):
    """
    Abstract class for periotic tasks. it requires to define 'timeout' and
    the method 'handle' that is called again and again infinitely with the
    set timeout.
    """

    # Timeout between 'handle' calls
    timeout = None

    def run(self):
        while True:
            logging.info(f"Handle task '{self.__class__.__name__}'")
            self.handle()
            sleep(self.timeout)

    def handle(self):
        """
        A handler for call periodically. Must be implemented.
        """
        raise NotImplementedError()


class TaskManager:
    """
    Implements task manager that runs registered tasks in separate processes.
    """

    def __init__(self):
        self._tasl_cls_list = []

    def register(self, task_cls):
        """
        Registers a task (as a decorator over the task class).
        """
        self._tasl_cls_list.append(task_cls)
        logging.debug(f"Task '{task_cls.__name__}' registered")
        return task_cls

    def run(self):
        """
        Creates processes for the registered tasks and runs them.
        """
        logging.info("Run task manager")
        processes = [
            mp.Process(target=self._run_task, args=(task_cls,))
            for task_cls in self._tasl_cls_list
        ]
        list(map(mp.Process.start, processes))
        list(map(mp.Process.join, processes))

    def _run_task(self, task_cls):
        logging.info(f"Run task '{task_cls.__name__}'")
        task_cls().run()
