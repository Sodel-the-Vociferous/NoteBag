## Miscellaneous Helpful Functions
# Written by Daniel Ralston

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import inspect
import os.path
from os.path import abspath, dirname, expanduser, realpath

def get_called_script_dir():
    """
    Return the directory that the top-level running script is in.
    """
    bottom_stack_frame = inspect.stack()[-1][0]
    called_script_path = inspect.getfile(bottom_stack_frame)
    return realpath(abspath(dirname(called_script_path)))

def get_config_path(filename):
    """
    Return the full path to a config file named <filename> in the same
    directory as the top-level running script.
    """
    config_dir = get_called_script_dir()
    config_path = os.path.join(config_dir, filename)
    config_path = realpath(abspath(expanduser(config_path)))
    return config_path

def read_config(filename):
    """
    Read a config file named <filename>, from the same directory as
    the top-level running script, using configparser.
    """
    config_path = get_config_path(filename)
    config = configparser.ConfigParser()
    config.read(config_path)
    return config

def save_config(config, filename):
    """
    Save a configparser configuration to <filename>, in the same
    directory as the top-level running script.
    """
    config_dir = get_called_script_dir()
    config_path = os.path.join(config_dir, filename)
    with open(config_path, 'w') as f:
        config.write(f)
