# libgolf
libgolf is a library of common utilities for writing golfing language builtins. It currently includes:

- `List`, a well-featured lazy list class
- `Character`, a thin wrapper for representing Unicode characters
- `String`, a wrapper around a `List` of `Character`s that behaves more like Python's [built-in `str`
  type](https://docs.python.org/3/library/stdtypes.html#str)
- `vectorise`, a higher-order function (or decorator) for automatically mapping a function over its arguments

libgolf aims to semi-standardise these features across golfing languages by allowing them to be shared, and provide high-quality code with unit tests
to ensure robustness of their implementations.
