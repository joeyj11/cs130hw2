from z3 import *

x0, x1, x2 = Ints('x0 x1 x2')

# solver
s = Solver()

# AllPositive constraint
s.add(x0 > 0, x1 > 0, x2 > 0)

# check if satisfied
if s.check() == sat:
    print("SAT")
    print(s.model())
else:
    print("UNSAT")
