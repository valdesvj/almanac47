"""ion.py - PC stand-in for the NumWorks ion module (preview only).
The keys come from a script: script = ['SHOT:file.png', 'KEY_UP', 'SHOT:b.png', 'KEY_BACK'].
A SHOT saves the kandinsky image; a key name reads as pressed once, then released.
When the script is used up, BACK is pressed.
Almanac 47. Copyright 2026 Victor Valdes. GPL-3.0-or-later."""
import kandinsky

_names = ('KEY_LEFT', 'KEY_UP', 'KEY_DOWN', 'KEY_RIGHT', 'KEY_OK', 'KEY_BACK',
          'KEY_HOME', 'KEY_ONOFF', 'KEY_SHIFT', 'KEY_ALPHA', 'KEY_XNT', 'KEY_VAR',
          'KEY_TOOLBOX', 'KEY_BACKSPACE', 'KEY_EXE')
for _i, _n in enumerate(_names):
    globals()[_n] = _i

script = []
_down = None                  # key reported as down until it is read once more


def keydown(k):
    global _down
    if _down is not None:
        if k == _down:
            _down = None      # read again: now released
        return False
    while script and script[0].startswith('SHOT:'):
        kandinsky.save(script.pop(0)[5:])
    name = script[0] if script else 'KEY_BACK'
    if globals()[name] == k:
        if script:
            script.pop(0)
        _down = k
        return True
    return False
