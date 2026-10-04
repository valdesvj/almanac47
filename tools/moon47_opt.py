#!/usr/bin/env python3
"""moon47_opt.py - DEV: MOON47 (tools/build_moon47.py) with the Moon as matrices, Horner and n-vectors
(tools/build_navopt.py writes build/dev/opt/MOON47_OPT.txt and free42/MOON47_OPT.txt with it).

  the 20 terms   built once per run into the matrix M7T (20 x 10: d m m' f, sin coefficient for |m| = 0 1 2,
                 cos coefficient for |m| = 0 1 2) from the same compact data (code, cl, cr) as the release;
                 then every Moon (LBL 41: the page, and each step of the secant search for the phases) is
                 M7T x [D M M' F 0 ...] -> SIN, COS of the 20 arguments, DOT with M7T x [0 0 0 0 1 E E² 0 0 0]
                 and M7T x [0 ... 0 1 E E²] (E^|m| as Horner weights): about 50 steps instead of 1000.
  the Sun        the equation of the centre by Clenshaw (Horner for a sine series: one →REC instead of
                 three SIN), the distance as a polynomial in cos M (one COS instead of two).
  n-vectors      R sin ψ and R cos ψ with one →REC.
At the end the four matrices become 0 (STO): their memory is free again.
  TZ             at the start: if the variable TZ is not there, MOON47 creates it with 0 (after the read
                 that ignores the missing variable, STO "TZ" stores what was read, or 0).
"""


def blk(s):
    return s.split('|')


def cut(L, old, new):
    s = '\n' + '\n'.join(L) + '\n'
    o = '\n' + '\n'.join(old) + '\n'
    assert s.count(o) == 1, 'moon47_opt: block not found once: %r' % old[:6]
    return s.replace(o, '\n' + '\n'.join(new) + '\n').strip('\n').split('\n')


L41_OLD = blk("LBL 41|0.000798611|+|2451545|-|36525|÷|STO 14|445267.1114|×|297.8501921|+|STO 10|RCL 14|35999.05029|×|357.5291092|+|STO 11|RCL 14|477198.8675|×|134.9633964|+|STO 12|RCL 14|483202.0175|×|93.272095|+|STO 13|RCL 14|0.004817|×|1.914602|X<>Y|-|RCL 11|SIN|×|RCL 11|2|×|SIN|0.019993|×|+|RCL 11|3|×|SIN|0.000289|×|+|STO 48|RCL 14|0.002516|×|1|X<>Y|-|STO 14|0|STO 40|STO 41")
L41_NEW = ['LBL 41', '2451544.999201389', '-', '36525', '÷', 'STO 14',
           '445267.1114', '×', '297.8501921', '+', 'STO 10',
           '35999.05029', 'RCL× 14', '357.5291092', '+', 'STO 11',
           '477198.8675', 'RCL× 14', '134.9633964', '+', 'STO 12',
           '483202.0175', 'RCL× 14', '93.272095', '+', 'STO 13',
           # the Sun's equation of the centre by Clenshaw: b2 = c2 + 2 cos M c3, b1 = c1 + 2 cos M b2 - c3, C = b1 sin M
           'RCL 11', '1', '→REC', '2', '×', 'STO 47', '0.000289', '×', '0.019993', '+', 'RCL× 47', '-0.000289', '+',
           '1.914602', '+', '-0.004817', 'RCL× 14', '+', '×', 'STO 48',
           '-0.002516', 'RCL× 14', '1', '+', 'STO 14',
           # the 20 terms as matrices: arguments, then Σ cl E^|m| sin and Σ cr E^|m| cos
           'INDEX "M7A"', 'RCL 10', 'STOEL', 'J+', 'RCL 11', 'STOEL', 'J+', 'RCL 12', 'STOEL', 'J+', 'RCL 13', 'STOEL',
           'INDEX "M7W"', '6', '1', 'STOIJ', 'RCL 14', 'STOEL', 'J+', 'RCL 14', 'X↑2', 'STOEL',
           'INDEX "M7V"', '9', '1', 'STOIJ', 'RCL 14', 'STOEL', 'J+', 'RCL 14', 'X↑2', 'STOEL',
           'RCL "M7T"', 'RCL "M7A"', '×', 'ENTER', 'SIN', 'RCL "M7T"', 'RCL "M7W"', '×', 'DOT', 'STO 40',
           'R↓', 'COS', 'RCL "M7T"', 'RCL "M7V"', '×', 'DOT', 'STO 41']


def l50_new():
    """LBL 51 (once per run): the matrices; LBL 50: one term (Z code, Y cl, X cr) into row R21 of M7T."""
    import build_moon47 as M
    P = ['REM "LBL 51: the matrix M7T of the 20 terms and the vectors M7A M7W M7V (once per run)"',
         'LBL 51', '20', 'ENTER', '10', 'NEWMAT', 'STO "M7T"', '10', 'ENTER', '1', 'NEWMAT', 'STO "M7A"', 'STO "M7W"', 'STO "M7V"',
         'INDEX "M7W"', '5', '1', 'STOIJ', '1', 'STOEL', 'INDEX "M7V"', '8', '1', 'STOIJ', '1', 'STOEL', '1', 'STO 21']
    P += M.terms() + ['RTN']
    P += ['REM "LBL 50: Z the multiples (code), Y cl, X cr -> row R21 of M7T: d m m\' f, cl in column 5 + |m|, cr in 8 + |m|"',
          'LBL 50', 'STO 43', 'R↓', 'STO 42', 'R↓', 'STO 44', 'INDEX "M7T"', 'RCL 21', '1', 'STOIJ',
          'RCL 44', '1000', '÷', 'IP', 'STOEL', 'J+',
          'RCL 44', '100', '÷', 'IP', '10', 'MOD', '1', '-', 'STO 45', 'STOEL', 'J+',
          'RCL 44', '10', '÷', 'IP', '10', 'MOD', '2', '-', 'STOEL', 'J+',
          'RCL 44', '10', 'MOD', '2', '-', 'STOEL',
          'RCL 21', 'RCL 45', 'ABS', '5', '+', 'STOIJ', 'RCL 42', 'STOEL',
          'RCL 21', 'RCL 45', 'ABS', '8', '+', 'STOIJ', 'RCL 43', 'STOEL', '1', 'STO+ 21', 'RTN']
    return P


L29_OLD = blk("RCL 22|COS|RCL 15|COS|×|ACOS|STO 16|RCL 11|COS|0.016708|×|1.00014|X<>Y|-|RCL 11|2|×|COS|0.000141|×|-|149597870.7|×|STO 17|RCL 16|SIN|×|STO 18|RCL 41|RCL 17|RCL 16|COS|×|-|STO 19|X↑2|RCL 18|X↑2|+|SQRT|RCL 19|X<>Y|÷|1|+|50|×|STO 18")
L29_NEW = ['RCL 15', 'RCL 22', 'COS', '→REC', 'ACOS', 'STO 16',                       # ψ: cos β cos e
           'RCL 11', 'COS', 'ENTER', 'ENTER', '-0.000282', '×', '-0.016708', '+', '×', '1.000281', '+',   # R (au), Horner in cos M
           '149597870.7', '×', 'STO 17', 'RCL 16', 'X<>Y', '→REC', 'RCL 41', 'X<>Y', '-', 'STO 19',
           'X↑2', 'X<>Y', 'X↑2', '+', 'SQRT', 'RCL 19', 'X<>Y', '÷', '1', '+', '50', '×', 'STO 18']
FREE = ['0', 'STO "M7T"', 'STO "M7A"', 'STO "M7W"', 'STO "M7V"']


def transform(P, f42):
    i = P.index('LBL 41')
    j = P.index('STO 41', i) + 1
    k = j
    while P[k] != 'RCL 41':                       # the 20 terms (code, cl, cr, XEQ 50)
        k += 1
    assert P[i:j] == L41_OLD and (k - j) == 80, 'moon47_opt: LBL 41 changed'
    P = P[:i] + L41_NEW + P[k:]
    a = P.index('LBL 50')
    b = P.index('RTN', P.index('STO+ 41', a)) + 1
    P = P[:a] + l50_new() + P[b:]
    P = cut(P, L29_OLD, L29_NEW)
    P = cut(P, ['STO 06', '0', 'STO 28'], ['STO 06', '0', 'STO 28', 'XEQ 51'])
    tz = ['RCL "TZ"', 'STO 03', 'CF 25' if f42 else "CF 'IGN1ER'"]
    P = cut(P, tz, tz + ['STO "TZ"'])                  # TZ, or 0 when it was not there: now it is
    end = 'CLST' if f42 else 'CLSTK'
    assert P.count(end) == 1
    k = P.index(end)
    return P[:k] + FREE + P[k:]


def build(M):
    """(C47 lines, Free42 lines) of MOON47 with the optimized main program."""
    orig = M.main_program
    M.main_program = lambda f42=False: transform(orig(f42), f42)
    try:
        plain = M.build()[0]
        f42 = M.build_f42()
    finally:
        M.main_program = orig
    return plain, f42
