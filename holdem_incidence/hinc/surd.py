"""Exact arithmetic in a real quadratic field Q(sqrt(d)), for profiles whose equilibrium
probabilities are quadratic surds.

``Surd(a, b, d)`` is a + b*sqrt(d) with a, b Fractions and d a fixed square-free integer > 1.  It
supports + - * / with ints, Fractions and Surds of the same d, and exact comparison (the sign of
a + b*sqrt(d) is decided by comparing a^2 with b^2 d, never by floating point).  That is all the
evaluation and best-response code (hinc/evaluate.py, hinc/bestresponse.py) uses on object arrays,
so a profile of Surds is evaluated exactly by the same code as a profile of Fractions
(tests/test_surd.py checks this).
"""
from __future__ import annotations

from fractions import Fraction
from math import isqrt, sqrt
from numbers import Rational


class Surd:
    __slots__ = ("a", "b", "d")

    def __init__(self, a, b=0, d=2):
        self.a = Fraction(a)
        self.b = Fraction(b)
        self.d = int(d)
        if self.d < 2 or isqrt(self.d) ** 2 == self.d:
            raise ValueError("d must be a non-square integer > 1")

    # --- coercion -------------------------------------------------------------------------------
    def _co(self, o):
        if isinstance(o, Surd):
            if o.d != self.d and o.b != 0 and self.b != 0:
                raise ValueError("Surds of different fields: sqrt(%d) and sqrt(%d)" % (self.d, o.d))
            return o.a, o.b
        if isinstance(o, (int, Rational)):
            return Fraction(o), Fraction(0)
        return None

    # --- field operations -----------------------------------------------------------------------
    def __add__(self, o):
        c = self._co(o)
        if c is None:
            return NotImplemented
        return Surd(self.a + c[0], self.b + c[1], self.d)

    __radd__ = __add__

    def __neg__(self):
        return Surd(-self.a, -self.b, self.d)

    def __sub__(self, o):
        c = self._co(o)
        if c is None:
            return NotImplemented
        return Surd(self.a - c[0], self.b - c[1], self.d)

    def __rsub__(self, o):
        c = self._co(o)
        if c is None:
            return NotImplemented
        return Surd(c[0] - self.a, c[1] - self.b, self.d)

    def __mul__(self, o):
        c = self._co(o)
        if c is None:
            return NotImplemented
        return Surd(self.a * c[0] + self.b * c[1] * self.d, self.a * c[1] + self.b * c[0], self.d)

    __rmul__ = __mul__

    def _inv(self):
        n = self.a * self.a - self.b * self.b * self.d       # norm; nonzero unless self == 0
        if n == 0:
            raise ZeroDivisionError("Surd division by zero")
        return Surd(self.a / n, -self.b / n, self.d)

    def __truediv__(self, o):
        c = self._co(o)
        if c is None:
            return NotImplemented
        return self * Surd(c[0], c[1], self.d)._inv()

    def __rtruediv__(self, o):
        c = self._co(o)
        if c is None:
            return NotImplemented
        return Surd(c[0], c[1], self.d) * self._inv()

    # --- exact order ----------------------------------------------------------------------------
    def sign(self):
        a, b = self.a, self.b
        if b == 0:
            return (a > 0) - (a < 0)
        if a == 0:
            return (b > 0) - (b < 0)
        if (a > 0) == (b > 0):
            return 1 if a > 0 else -1
        bigger = a * a > b * b * self.d                       # |a| vs |b| sqrt(d)
        return (1 if a > 0 else -1) if bigger else (1 if b > 0 else -1)

    def _cmp(self, o):
        c = self._co(o)
        if c is None:
            return None
        return Surd(self.a - c[0], self.b - c[1], self.d).sign()

    def __eq__(self, o):
        s = self._cmp(o)
        return NotImplemented if s is None else s == 0

    def __lt__(self, o):
        s = self._cmp(o)
        return NotImplemented if s is None else s < 0

    def __le__(self, o):
        s = self._cmp(o)
        return NotImplemented if s is None else s <= 0

    def __gt__(self, o):
        s = self._cmp(o)
        return NotImplemented if s is None else s > 0

    def __ge__(self, o):
        s = self._cmp(o)
        return NotImplemented if s is None else s >= 0

    def __hash__(self):
        return hash((self.a, self.b, self.d)) if self.b != 0 else hash(self.a)

    def __bool__(self):
        return self.a != 0 or self.b != 0

    # --- display ----------------------------------------------------------------------------------
    def __float__(self):
        return float(self.a) + float(self.b) * sqrt(self.d)

    def __str__(self):
        if self.b == 0:
            return str(self.a)
        return "%s + %s*sqrt(%d)" % (self.a, self.b, self.d)

    __repr__ = __str__


def parse(text: str):
    """Inverse of str(): 'p/q' -> Fraction, 'a + b*sqrt(d)' -> Surd."""
    if "sqrt" not in text:
        return Fraction(text)
    a, rest = text.split(" + ")
    b, d = rest.split("*sqrt(")
    return Surd(Fraction(a), Fraction(b), int(d.rstrip(")")))
