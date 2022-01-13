"""
Endpoint to run task_manager defined in service/tasks.py
"""

from service.tasks import task_manager


if __name__ == "__main__":
    task_manager.run(restart=True)
