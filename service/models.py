# Import implemented models.
# It is recommended to import models (for example: Proxy or Node)
# from the module 'models', not directly.
#     Example: from .models import Proxy, Node
from .proxy import Proxy
from .node import Node

# Encure the table for Proxy in the database
from .db import Base, engine
Base.metadata.create_all(engine)
