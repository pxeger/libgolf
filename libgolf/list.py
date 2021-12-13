import itertools
import functools


# helper singleton for lexicographic comparisons
_fill = object()


class List:
    @classmethod
    def wrap(cls, func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            return cls(func(*args, **kwargs))
        return inner

    @staticmethod
    def _wrap(func):
        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return type(self)(func(self, *args, **kwargs))
        return inner

    @staticmethod
    def _classmethod_wrap(func):
        @classmethod
        @functools.wraps(func)
        def inner(cls, *args, **kwargs):
            return cls(func(*args, **kwargs))
        return inner

    def __init__(self, i=()):
        self.cache = []
        self.finished = False
        self.it = iter(i)

    def __iter__(self):
        if self.finished:
            yield from self.cache
            return
        i = 0
        while True:
            # yield any values from the cache that may have been put there by concurrent iteration of self
            while i < len(self.cache):
                yield self.cache[i]
                i += 1
            try:
                self.cache.append(next(self.it))
            # can't propogate StopIteration in a generator; have to catch and return explicitly
            except StopIteration as e:
                self.finished = True
                return e.value

    def exhaust(self):
        if not self.finished:
            self.cache.extend(self.it)
            self.finished = True

    def __reversed__(self):
        self.exhaust()
        # TODO(pxeger): must this return an iterator specifically, not just an iterable?
        return type(self)(reversed(self.cache))

    def __len__(self):
        self.exhaust()
        return len(self.cache)

    def length_compare_length(self, other):
        for x, y in itertools.zip_longest(self, other, fillvalue=_fill):
            if x is _fill:
                # self is shorter than other
                return -1
            elif y is _fill:
                # other is shorter than self
                return +1
        return 0

    def length_compare_int(self, n: int):
        return self.length_compare_length(self.nones(n))

    @_classmethod_wrap
    def nones(length=-1):
        if length < 0:
            while True:
                yield None
        else:
            for _ in range(length):
                yield None

    def __repr__(self):
        return repr(list(self))

    def __getitem__(self, arg):
        if isinstance(arg, slice):
            return self._slice(arg)

        # fast paths
        if arg in range(len(self.cache)):
            return self.cache[arg]
        elif self.finished:
            return self.cache[arg % len(self.cache)]

        elif arg < 0:
            # negative index necessitates exhausting iterator
            self.exhaust()
            return self.cache[arg]
        else:
            # this loop allows modular indexing without needing to exhaust self
            # (with the caveat that this is now O(n) - hence the fast paths above, to avoid that)
            i = iter(self._loop())
            for _ in range(arg):
                next(i)
            return next(i)

    def _loop(self):
        while True:
            yield from self

    @_wrap
    def _slice(self, s):
        if s.step is not None and s.step < 0:
            # since we have to enumerate all elements anyway, there's no better way than with exhaust
            self.exhaust()
            return self.cache[s]
        else:
            return itertools.islice(self, s.start, s.stop, s.step)

    # comparison operators are always as lazy as possible

    def __eq__(self, other):
        # fast path
        if self is other:
            return True

        try:
            other = type(self)(other)
        except TypeError:
            return NotImplemented

        try:
            return all(x == y for x, y in zip(self, other, strict=True))
        except ValueError:
            # strict zip failed; lengths were different
            return False

    def __ne__(self, other):
        # fast path
        if self is other:
            return False

        try:
            other = type(self)(other)
        except TypeError:
            return NotImplemented

        try:
            return any(x != y for x, y in zip(self, other, strict=True))
        except ValueError:
            # strict zip failed; lengths were different
            return True

    def __lt__(self, other):
        # fast path
        if self is other:
            return False

        try:
            other = type(self)(other)
        except TypeError:
            return NotImplemented

        for x, y in itertools.zip_longest(self, other, fillvalue=_fill):
            if x is _fill:
                # self is shorter than other
                return True
            elif y is _fill:
                # other is shorter than self
                return False
            elif x < y:
                return True
            elif x > y:
                return False
        # all completely equal
        return False

    def __le__(self, other):
        # fast path
        if self is other:
            return True

        try:
            other = type(self)(other)
        except TypeError:
            return NotImplemented

        for x, y in itertools.zip_longest(self, other, fillvalue=_fill):
            if x is _fill:
                # self is shorter than other
                return True
            elif y is _fill:
                # other is shorter than self
                return False
            elif x < y:
                return True
            elif x > y:
                return False
        # all completely equal
        return True

    def __gt__(self, other):
        # fast path
        if self is other:
            return False

        try:
            other = type(self)(other)
        except TypeError:
            return NotImplemented

        for x, y in itertools.zip_longest(self, other, fillvalue=_fill):
            if x is _fill:
                # self is shorter than other
                return False
            elif y is _fill:
                # other is shorter than self
                return True
            elif x < y:
                return False
            elif x > y:
                return True
        # all completely equal
        return False

    def __ge__(self, other):
        # fast path
        if self is other:
            return True

        try:
            other = type(self)(other)
        except TypeError:
            return NotImplemented

        for x, y in itertools.zip_longest(self, other, fillvalue=_fill):
            if x is _fill:
                # self is shorter than other
                return False
            elif y is _fill:
                # other is shorter than self
                return True
            elif x < y:
                return False
            elif x > y:
                return True
        # all completely equal
        return True

    @_wrap
    def find_substrings(self, pattern):
        # naïve substring search, Θ(mn), but it's not easy to get better when you have to be lazy
        pattern = type(self)(pattern)
        i = 0
        while True:
            iterator = iter(self)
            try:
                for _ in range(i):
                    next(iterator)
            except StopIteration:
                break
            for item in pattern:
                if next(iterator, _fill) != item:
                    i += 1
                    break
            else:
                # did not break; all were equal
                yield i
                i += max(1, len(pattern))

    @_wrap
    def replace(self, pattern, replacement, maxcount=-1):
        # fast paths
        if self is pattern:
            yield from replacement
            return
        elif pattern is replacement:
            yield from self
            return
        elif maxcount == 0:
            yield from self
            return

        prev = 0
        for index in self.find_substrings(pattern):
            yield from self[prev:index]
            yield from replacement
            prev = index + len(pattern)
            if maxcount > 0:
                maxcount -= 1
                if maxcount == 0:
                    break
        yield from self[prev:]

    @_wrap
    def replace_instances(self, find, replacement, maxcount=-1):
        if find is replacement:
            yield from self
            return 0
        elif maxcount == 0:
            yield from self
            return 0

        for i in self:
            if i == find:
                yield replacement
                if maxcount > 0:
                    maxcount -= 1
                    if maxcount == 0:
                        yield from self
                        return 0
            else:
                yield i

    @_wrap
    def unique(self):
        known = []
        # optimisation for hashable items
        known_fast = set()
        for item in self:
            try:
                if item in known_fast:
                    continue
                else:
                    known_fast.add(item)
            except TypeError:
                if item in known:
                    continue
                else:
                    known.append(item)

            yield item

    @classmethod
    def product(cls, *iterables):
        def closure_hack(result, iterable):
            # by defining result and iterable as parameters to an inner function, they won't be closed over
            return ((*xs, y) for xs in result for y in iterable)

        result = ((),)
        for iterable in iterables:
            result = cls(closure_hack(result, cls(iterable)))
        # wrap each tuple in a List (or, well, a cls)
        return cls(cls(t) for t in result)

    def power(self, power):
        return self.product(*(self for _ in range(power)))

    @_wrap
    def combinations(self, size):
        if size <= 0:
            return
        result = [None] * size
        stack = [0]
        while stack:
            result_index = len(stack) - 1
            input_index = stack.pop()
            while self.length_compare_int(input_index) == 1:
                result[result_index] = self[input_index]
                result_index += 1
                input_index += 1
                stack.append(input_index)
                if result_index == size:
                    yield List(result)
                    break
