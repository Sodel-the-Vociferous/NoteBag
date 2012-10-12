## Miscellaneous Helpful Functions
# Written by Daniel Ralston

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import inspect
import os.path
from os.path import abspath, dirname, realpath

def get_called_script_dir():
    bottom_stack_frame = inspect.stack()[-1][0]
    called_script_path = inspect.getfile(bottom_stack_frame)
    return realpath(abspath(dirname(called_script_path)))

def read_config(filename):
    config_dir = get_called_script_dir()
    config_path = os.path.join(config_dir, filename)

    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def save_config(config, filename):
    config_dir = get_called_script_dir()
    config_path = os.path.join(config_dir, filename)
    with open(config_path, 'w') as f:
        config.write(f)
