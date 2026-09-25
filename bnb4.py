"""bnb3 + an arbitrary extra box-pruning predicate (for targeted questions)."""
import numpy as np, bnb2, bnb3
U, MIX, DC = bnb2.U, bnb2.MIX, bnb2.DC

def search(lab0, order, extra=None, nsplit=2, bdepth=8, cap=2048,
           maxnodes=None, sink=None, log=None):
    prop = bnb2.propagate
    def P(a, b, c):
        a, b, c, al = prop(a, b, c)
        if extra is not None and al.any():
            al &= ~extra(a, b, c)
        return a, b, c, al
    import types
    m = types.ModuleType("tmp"); 
    # reuse bnb3.search but with our propagate
    old = bnb3.propagate
    bnb3.propagate = P
    try:
        return bnb3.search(lab0, order, nsplit=nsplit, bdepth=bdepth, cap=cap,
                           maxnodes=maxnodes, sink=sink, log=log)
    finally:
        bnb3.propagate = old
