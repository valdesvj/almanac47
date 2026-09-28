AGRAPH with the pattern in stack register T (font speed test)
=============================================================
Each font column is now 4 steps:  pattern  STO 32  R↓  AGRAPH 32
If AGRAPH can read the pattern from stack register T it is 3:  pattern  R↓  AGRAPH ST.T
(after R↓: X = column, Y = row, T = pattern).

AGT1, AGT2 and AGT3 are the same test, the stack register written three ways
(ST.T, ST T, 103 = register number of T). Convert each with rejig; keep the one that loads.
XEQ it: two small U shapes (3 columns: tall bar, short foot, tall bar) at row 100,
the left one drawn the usual way (column 50), the right one with the stack register (column 70).
Both the same: the fonts can be made about 25 % faster.  Right one missing or different: no.

Result on the calculator: AGT1 and AGT2 do not load; AGT3 loads but 103 is taken as the
variable "g". Keyed by hand, AGRAPH D works (8-level stack: R↓ puts the pattern in D, not T).
In the text files the register is written by name: AGRAPH D. The NAV fonts now use it.

