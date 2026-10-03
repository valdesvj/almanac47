#!/usr/bin/env python3
"""c47ref.py - the C47 command table from the C47 firmware source (gitlab rpncalculators/c43, master).

The web reference (47calc.com) follows the official releases only; the firmware on master is ahead of it
(GRMOD, ATEXT, GRFNT came there first). So the reference for this project is read from a local clone
of the firmware source, at whatever commit it is on:

  src/c47/items.c   indexOfItems[]: per item the function, parameter, catalog name, softmenu name, TAM range
                    and flags (category, stack lift, programmability)
  src/c47/items.h   the ITM_ names of the item numbers
  src/c47/fonts.h   the STD_ macros in the names (other string macros: the other headers, items.c); two bytes \\xHH\\xLL are the code point
                    (HH & 0x7F) * 256 + LL (charString.c, stringToUtf8)

  python3 tools/c47ref.py [C43_DIR]      writes docs/reference/C47_items_master.tsv
                                         (C43_DIR default: $C43_DIR or ~/opt/c43)
  python3 tools/c47ref.py --check [C43_DIR]
                                         only reports whether the table matches the clone (exit 1 if not)

Run it after every git pull in the clone. The table is data parsed from GPL-3.0 source.
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'docs', 'reference', 'C47_items_master.tsv')
COLS = ['opcode', 'itm', 'catalog_name', 'softmenu_name', 'function', 'param', 'tam_max', 'tam_value',
        'category', 'programmable', 'stack_lift', 'rejig_name', 'rejig_bytes', 'rejig_aliases']


def c43_dir(arg=None):
    return os.path.expanduser(arg or os.environ.get('C43_DIR') or '~/opt/c43')


def git(c43, *a):
    return subprocess.run(['git', '-C', c43] + list(a), capture_output=True, text=True, check=True).stdout.strip()


def c_bytes(lit):
    """The bytes of one C string literal body (escapes \\xHH, \\ooo, \\n, \\", \\\\)."""
    out = bytearray(); i = 0
    while i < len(lit):
        ch = lit[i]
        if ch != '\\':
            out += ch.encode('utf-8'); i += 1; continue
        n = lit[i + 1]
        if n == 'x':
            m = re.match(r'[0-9a-fA-F]{1,2}', lit[i + 2:]); out.append(int(m.group(), 16)); i += 2 + len(m.group())
        elif n in '01234567':
            m = re.match(r'[0-7]{1,3}', lit[i + 1:]); out.append(int(m.group(), 8)); i += 1 + len(m.group())
        else:
            out += {'n': b'\n', 't': b'\t', '"': b'"', '\\': b'\\', "'": b"'", '0': b'\0'}[n]; i += 2
    return bytes(out)


TOKEN = re.compile(r'\s*(?:"((?:[^"\\]|\\.)*)"|([A-Za-z_]\w*))')


def c_concat(expr, macros):
    """Bytes of a concatenation of string literals and string macros, e.g. "x" STD_NOT_EQUAL " ?"."""
    out = b''; pos = 0; expr = expr.strip()
    while pos < len(expr):
        m = TOKEN.match(expr, pos)
        if not m:
            raise ValueError('cannot read %r' % expr)
        out += c_bytes(m.group(1)) if m.group(1) is not None else macros[m.group(2)]
        pos = m.end()
    return out


def c47_to_utf8(b):
    """C47 string bytes -> text: an ASCII byte is itself, two bytes with the high bit set are one code point."""
    s = []; i = 0
    while i < len(b):
        if b[i] & 0x80:
            s.append(chr((b[i] & 0x7F) * 256 + b[i + 1])); i += 2
        else:
            s.append(chr(b[i])); i += 1
    return ''.join(s)


def read_macros(c43):
    macros = {}
    d = os.path.join(c43, 'src/c47')
    files = ['fonts.h'] + sorted(f for f in os.listdir(d) if f.endswith('.h') and f != 'fonts.h') + ['items.c']
    for ln in (l for f in files for l in open(os.path.join(d, f), encoding='utf-8', errors='replace')):
        m = re.match(r'\s*#define\s+(\w+)\s+((?:"(?:[^"\\]|\\.)*"\s*|[A-Za-z_]\w*\s*)+)(?://.*)?$', ln)
        if m:
            try:
                macros[m.group(1)] = c_concat(m.group(2), macros)
            except (KeyError, ValueError):
                pass
    return macros


def split_top(s):
    """Split a C initializer body at the commas outside quotes and brackets."""
    parts = []; depth = 0; q = False; cur = ''; i = 0
    while i < len(s):
        ch = s[i]
        if q:
            cur += ch
            if ch == '\\':
                cur += s[i + 1]; i += 1
            elif ch == '"':
                q = False
        elif ch == '"':
            q = True; cur += ch
        elif ch in '({':
            depth += 1; cur += ch
        elif ch in ')}':
            depth -= 1; cur += ch
        elif ch == ',' and depth == 0:
            parts.append(cur.strip()); cur = ''
        else:
            cur += ch
        i += 1
    if cur.strip():
        parts.append(cur.strip())
    return parts


def read_items(c43):
    macros = read_macros(c43)
    itm = {}
    for ln in open(os.path.join(c43, 'src/c47/items.h'), encoding='utf-8', errors='replace'):
        m = re.match(r'\s*#define\s+(ITM_\w+)\s+(\d+)\b', ln)
        if m:
            itm.setdefault(int(m.group(2)), []).append(m.group(1))
    src = open(os.path.join(c43, 'src/c47/items.c'), encoding='utf-8', errors='replace').read()
    body = src[src.index('indexOfItems[] = {'):]
    rows = []
    for m in re.finditer(r'^/\*\s*(\d+)\s*\*/\s*(?:\{(.*)\}|UNIT_CONV\((.*)\)),?\s*(?://.*)?$', body, re.M):
        n = int(m.group(1))
        if m.group(2) is not None:
            fn, param, cat_name, menu_name, tam, flags = split_top(re.sub(r'/\*.*?\*/', ' ', m.group(2)))[:6]
        else:                                               # UNIT_CONV(unit, invert, cat, menu), items.c
            unit, inv, cat_name, menu_name = split_top(re.sub(r'/\*.*?\*/', ' ', m.group(3)))[:4]
            fn, param, tam = 'fnUnitConvert', unit + ' | ' + inv, '(0 << TAM_MAX_BITS) | 0'
            flags = 'CAT_NONE | SLS_ENABLED | US_ENABLED | EIM_DISABLED | PTP_NONE | RESULT_IN_X'
        cat_name = c47_to_utf8(c_concat(cat_name, macros)); menu_name = c47_to_utf8(c_concat(menu_name, macros))
        if fn == 'itemToBeCoded' and n and (menu_name in ('', str(n)) or re.fullmatch(r'\d+', menu_name)):
            continue                                        # a spare slot
        t = re.match(r'\((\w+)\s*<<\s*TAM_MAX_BITS\)\s*\|\s*(\w+)', tam)
        fl = [f.strip() for f in flags.split('|')]
        rows.append([str(n), ' '.join(itm.get(n, [])), cat_name, menu_name, fn, param.strip(),
                     t.group(1) if t else '', t.group(2) if t else tam,
                     next((f for f in fl if f.startswith(('CAT_', 'ATX_', 'ATF_'))), ''),
                     next((f for f in fl if f.startswith('PTP_')), ''),
                     next((f for f in fl if f.startswith('SLS_')), '')])
    return rows


def rejig_path():
    return os.environ.get('REJIG') or shutil.which('rejig') or ''


def read_rejig():
    """rejig --ops=r47: {opcode: (name, bytes, aliases)} and the version; empty without a rejig."""
    r = rejig_path()
    if not r:
        return {}, 'no rejig'
    ver = subprocess.run([r, '--version'], capture_output=True, text=True).stdout.strip()
    ops = {}
    for ln in subprocess.run([r, '--ops=r47'], capture_output=True, text=True, check=True).stdout.splitlines()[1:]:
        p = ln.split('\t')
        if len(p) >= 5 and p[0].isdigit():
            ops[int(p[0])] = (p[2], p[1], '' if p[4] == 'none' else p[4])
    return ops, ver


def header(c43, rver):
    return ['# C47 items (commands, functions, characters, menus) parsed from the firmware source by tools/c47ref.py',
            '# source: gitlab.com/rpncalculators/c43 %s, commit %s (%s), %s' % (
                git(c43, 'rev-parse', '--abbrev-ref', 'HEAD'), git(c43, 'rev-parse', '--short=9', 'HEAD'),
                git(c43, 'log', '-1', '--format=%ci'), git(c43, 'describe', '--tags', '--always')),
            '# rejig columns: rejig %s --ops=r47, joined by item number (blank: this rejig cannot write the item)' % rver,
            '# data parsed from GPL-3.0-only source (src/c47/items.c, items.h, fonts.h); spare slots left out',
            '# catalog_name / softmenu_name: as the firmware stores them (its own code points: x² is xⅢ);',
            '#   rejig_name: the Unicode name the .txt programs use; programmable: PTP_DISABLED = not in programs',
            '\t'.join(COLS)]


def table(c43):
    ops, rver = read_rejig()
    rows = [r + list(ops.get(int(r[0]), ('', '', ''))) for r in read_items(c43)]
    return '\n'.join(header(c43, rver) + ['\t'.join(r) for r in rows]) + '\n'


def load(path=OUT):
    """The saved table: list of row dicts."""
    return [dict(zip(COLS, ln.rstrip('\n').split('\t'))) for ln in open(path, encoding='utf-8')
            if not ln.startswith('#') and not ln.startswith('opcode\t')]


def program_names(rows):
    """{name or alias usable in a .txt program: row} (rejig names and aliases, plus the firmware names)."""
    names = {}
    for r in rows:
        for k in [r['rejig_name']] + r['rejig_aliases'].split() + [r['catalog_name']]:
            if k:
                names.setdefault(k, r)
    return names


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--check']
    c43 = c43_dir(a[0] if a else None)
    new = table(c43)
    if '--check' in sys.argv:
        old = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        print('up to date with %s' % new.split('\n')[1][10:] if old == new else 'OUT OF DATE: run python3 tools/c47ref.py')
        sys.exit(0 if old == new else 1)
    old = {r['opcode']: r['catalog_name'] for r in load()} if os.path.exists(OUT) else None
    open(OUT, 'w', encoding='utf-8').write(new)
    rows = load()
    print('%s: %d items, %d programmable, %d known to rejig' % (
        os.path.relpath(OUT), len(rows), sum(r['programmable'] != 'PTP_DISABLED' for r in rows),
        sum(bool(r['rejig_name']) for r in rows)))
    print('  ' + new.split('\n')[1][2:])
    if old is not None:
        cur = {r['opcode']: r['catalog_name'] for r in rows}
        ch = ['%s %s -> %s' % (k, old.get(k, '(new)'), cur.get(k, '(gone)')) for k in sorted(set(old) | set(cur), key=int)
              if old.get(k) != cur.get(k)]
        print('  changed since the last table: %s' % ('; '.join(ch) if ch else 'nothing'))
