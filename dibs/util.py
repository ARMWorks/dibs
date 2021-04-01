import base64
import pickle
from collections import OrderedDict
from functools import wraps
from subprocess import run

functions = {}

def call(data):
    data = base64.b64decode(data)
    function, args, kwargs = pickle.loads(data)
    if function not in functions:
        return
    return functions[function](*args, **kwargs)

def sudo(func):
    function = func.__name__
    functions[function] = func
    @wraps(func)
    def wrapper(*args, **kwargs):
        data = pickle.dumps((function, args, kwargs))
        data = base64.b64encode(data).decode('ascii')
        return run(['sudo', 'python', '-m', 'dibs', 'sudo', data]).returncode
    return wrapper

def zip_dicts(*dicts):
    return [(k, tuple(d.get(k) for d in dicts)) for k in
            OrderedDict.fromkeys(k for d in dicts for k in d)]
