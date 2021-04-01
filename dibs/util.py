from collections import OrderedDict

def zip_dicts(*dicts):
    return [(k, tuple(d.get(k) for d in dicts)) for k in
            OrderedDict.fromkeys(k for d in dicts for k in d)]
