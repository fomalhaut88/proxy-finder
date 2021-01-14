"""
Endpoint to run Flask API defined in service/api.py
"""

from service.api import app


if __name__ == "__main__":
    app.run()
