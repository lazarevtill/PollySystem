import importlib
import os
from fastapi import FastAPI

def load_plugins(app: FastAPI):
    plugins_dir = os.path.dirname(__file__)
    for item in os.listdir(plugins_dir):
        if item.startswith("__"):
            continue
        full_path = os.path.join(plugins_dir, item)
        if os.path.isdir(full_path):
            routes_file = os.path.join(full_path, "routes.py")
            if os.path.exists(routes_file):
                module_name = f"app.plugins.{item}.routes"
                mod = importlib.import_module(module_name)
                if hasattr(mod, "register"):
                    mod.register(app)
