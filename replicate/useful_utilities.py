#!/usr/bin/env python
from functools import wraps


def debug_func(func):
    from pprint import pprint

    @wraps(func)
    def wrapper(*args, **kwargs):
        print("ARGS:")
        pprint(args)
        print("KWARGS:")
        pprint(kwargs)
        print("DONE: {}".format(func.__name__))
        res = func(*args, **kwargs)
        print("RESULT: {}".format(res.__str__()))
        return res

    return wrapper


def timeit(func):
    import time

    @wraps(func)
    def wrapper(*args, **kwargs):
        print("Executing {}...".format(func.__name__))
        start_time = time.time()
        res = func(*args, **kwargs)
        end_time = time.time()
        print("Executing time:")
        print(end_time - start_time)
        return res

    return wrapper
