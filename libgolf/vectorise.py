from libgolf.list import List


def vectorise(function):
    def inner(*args):
        if not any(isinstance(arg, List) for arg in args):
            return function(*args)
        else:
            args = (arg if isinstance(arg, List) else List.repeat(arg) for arg in args)
            return List(map(inner, *args))
    return inner
