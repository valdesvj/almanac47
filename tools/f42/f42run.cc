// f42run - headless Free42 (SwissMicros core 3.3.10, binary math) for testing programs.
// The DM42 graphics modes (GrMod 2/3, 400x240) are drawn into a frame buffer.
// Commands on stdin, one per line:
//   paste FILE        add the program listing in FILE (as Free42 Paste in PRGM mode)
//   list N            print program N (0-based) as text (Free42 Copy)
//   xeq NAME          XEQ "NAME" and run until the program waits or stops
//   num VALUE         key a number and R/S (answers INPUT / continues after STOP)
//   key CODE          press a key (GETKEY code 1..37) and run on
//   shot FILE         write the 400x240 screen as a PBM
//   msg               print the 2-line display text (131x16) as ASCII art
//   export FILE       export all programs to a .raw file
//   stack             print X Y Z T and ALPHA
//   steps             print the number of program steps run so far
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include "core_main.h"
#include "core_globals.h"
#include "core_display.h"
#include "core_helpers.h"
#include "shell.h"

static unsigned char fb[240][400];
static unsigned char shown[240][400];        // what the LCD shows: fb when RefLCD bit 0 is set, else at RF
extern "C" int get_reflcd_mask();
static unsigned char lcd[16][131];
static bool want_t3 = false;
long long nsteps = 0;

const char *shell_platform() { return "f42run"; }
void shell_blitter(const char *bits, int bpl, int x, int y, int w, int h) {
    for (int r = y; r < y + h && r < 16; r++)
        for (int c = x; c < x + w && c < 131; c++)
            lcd[r][c] = (bits[r * bpl + (c >> 3)] >> (c & 7)) & 1;
}
void shell_beeper(int) {}
void shell_annunciators(int, int, int, int, int, int) {}
static long wcpu = 0;
bool shell_wants_cpu() { return (++wcpu & 1023) == 0; }
void shell_delay(int) {}
void shell_request_timeout3(int) { want_t3 = true; }
uint8 shell_get_mem() { return 100000000; }
bool shell_low_battery() { return false; }
void shell_powerdown() {}
int8 shell_random_seed() { return 12345; }
uint4 shell_milliseconds() { struct timeval tv; gettimeofday(&tv, 0); return (uint4) ((tv.tv_sec % 1000000) * 1000 + tv.tv_usec / 1000); }
const char *shell_number_format() { return "."; }
int shell_date_format() { return 2; }      // Y.MD
bool shell_clk24() { return true; }
void shell_print(const char *, int, const char *, int, int, int, int, int) {}

void shell_get_time_date(uint4 *time, uint4 *date, int *weekday) {
    struct timeval tv; gettimeofday(&tv, 0);
    long s = tv.tv_sec % 86400;
    if (time) *time = (s / 3600) * 1000000 + (s / 60 % 60) * 10000 + (s % 60) * 100 + tv.tv_usec / 10000;
    if (date) *date = 20260926;
    if (weekday) *weekday = 6;
}
void shell_message(const char *m) { fprintf(stderr, "MSG %s\n", m); }
void shell_log(const char *m) { fprintf(stderr, "LOG %s\n", m); }
void shell_malloc_fail(size_t, const char *, int) {}
double shell_vbat() { return 3.0; }
int shell_dev_id() { return 42; }
void shell_force_lcd_refresh(int what) { if (what & 1) memcpy(shown, fb, sizeof fb); }
void thell_draw_menu_key(int, int, const char *, int) {}
void thell_draw_char(int, int, char) {}
void thell_draw_pattern(int x, int y, const char *p, int w, int mode) {
    for (int h = 0; h < w; h++) {
        unsigned char c = p[h];
        for (int v = 0; v < 8; v++, c >>= 1) {
            int X = x + h, Y = y + v;
            if (X < 0 || X >= 400 || Y < 0 || Y >= 240) continue;
            int b = c & 1;
            switch (mode) {
                case 0: if (b) fb[Y][X] = 1; break;
                case 1: fb[Y][X] = b; break;
                case 2: if (b) fb[Y][X] = 0; break;
                case 3: if (b) fb[Y][X] ^= 1; break;
            }
        }
    }
}
void thell_draw_pixel(int x, int y) { if (x >= 0 && x < 400 && y >= 0 && y < 240) fb[y][x] = 1; }
void thell_clear_display() { memset(fb, 0, sizeof fb); }
void thell_clear_row(int) {}
void thell_start_show() {}
void thell_edit_number(const char *, int, const char *, int) {}

static int qkey = 0; static uint4 qtime = 0; static char qshot[512] = "";
static void shotbuf(const char *a, unsigned char (*b)[400]) {
    FILE *f = fopen(a, "wb"); fprintf(f, "P1\n400 240\n");
    for (int y = 0; y < 240; y++) { for (int x = 0; x < 400; x++) fputc(b[y][x] ? '1' : '0', f); fputc('\n', f); }
    fclose(f);
}
static void shot(const char *a) { shotbuf(a, fb); }
static void lcdshot(const char *a) { if (get_reflcd_mask() & 1) memcpy(shown, fb, sizeof fb); shotbuf(a, shown); }
static uint4 stime = 0; static char sfile[512] = ""; static int sseq = 0; static long severy = 0, scount = 0;
static void run(bool going) {
    bool enq; int rep;
    long guard = 0;
    while (true) {
        while (going) {
            if (sfile[0] && (severy ? ++scount % severy == 0 : shell_milliseconds() >= stime)) {        // captures while running: FILE_0.pbm, _1 ...
                char f[600]; snprintf(f, sizeof f, "%s_%d.pbm", sfile, sseq++); lcdshot(f);
                stime = shell_milliseconds() + 250;
                if (sseq >= 400) sfile[0] = 0;
            }
            if (qkey && shell_milliseconds() >= qtime) {       // a key pressed while the program runs
                int k = qkey; qkey = 0;
                if (qshot[0]) { shot(qshot); qshot[0] = 0; }
                going = core_keydown(k, &enq, &rep);
                if (!enq) going = core_keyup() || going; else core_keyup();
                continue;
            }
            going = core_keydown(0, &enq, &rep);
            if (getenv("F42DBG") && guard % 2000000 == 0) fprintf(stderr, "run prgm %d pc %d ms %u q %d/%u\n", current_prgm, (int) pc, shell_milliseconds(), qkey, qtime);
            if (++guard > 400000000) { fprintf(stderr, "guard\n"); return; }
        }
        if (want_t3) { want_t3 = false; going = core_timeout3(true); if (going) continue; }
        break;
    }
}
static void press(int k) {
    bool enq; int rep;
    bool going = core_keydown(k, &enq, &rep);
    if (!enq) going = core_keyup() || going;
    run(going);
}

int main() {
    core_init(0, 0, NULL, 0);
    char line[4096];
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\r\n")] = 0;
        char *a = strchr(line, ' ');
        if (a) *a++ = 0; else a = line + strlen(line);
        if (!strcmp(line, "paste")) {
            FILE *f = fopen(a, "rb"); if (!f) { printf("no file %s\n", a); continue; }
            fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
            char *buf = (char *) malloc(n + 1); fread(buf, 1, n, f); buf[n] = 0; fclose(f);
            if (!flags.f.prgm_mode) { press(28); press(36); }        // shift R/S = PRGM
            core_paste(buf);
            press(33);                                             // EXIT
            if (flags.f.prgm_mode) press(33);
            printf("pasted %s: %d programs\n", a, prgms_count);
            free(buf);
        } else if (!strcmp(line, "list")) {
            int n = atoi(a);
            int save = current_prgm; current_prgm = n;
            press(28); press(36);
            char *t = core_copy();
            press(33);
            current_prgm = save;
            printf("%s\n", t); free(t);
        } else if (!strcmp(line, "xeq")) {
            bool enq; int rep;
            // XEQ "name" as a one-line program at the end? no: set the program counter
            arg_struct arg; arg.type = ARGTYPE_STR; arg.length = strlen(a);
            memcpy(arg.val.text, a, arg.length);
            int prgm; int4 lpc;
            if (!find_global_label(&arg, &prgm, &lpc)) { printf("no label %s\n", a); continue; }
            current_prgm = prgm; pc = lpc;
            clear_all_rtns();
            press(36);                                             // R/S
        } else if (!strcmp(line, "num")) {
            char *s = a;
            for (; *s; s++) {
                int k = 0;
                if (*s >= '1' && *s <= '9') k = "\x1d\x1e\x1f\x18\x19\x1a\x13\x14\x15"[*s - '1'];
                else if (*s == '0') k = 34; else if (*s == '.') k = 35; else if (*s == '-') k = 15;
                if (k) { bool enq; int rep; core_keydown(k, &enq, &rep); core_keyup(); }
            }
            press(36);                                             // R/S
        } else if (!strcmp(line, "qkey")) {                  // qkey CODE MS: then a key while running
            int c, ms; qshot[0] = 0; sscanf(a, "%d %d %511s", &c, &ms, qshot); qkey = c; qtime = shell_milliseconds() + ms;
        } else if (!strcmp(line, "film")) {                  // film PREFIX: a capture every 0.25 s while running
            sseq = 0; severy = 0; sscanf(a, "%511s %ld", sfile, &severy); stime = shell_milliseconds();
        } else if (!strcmp(line, "stopfilm")) {
            sfile[0] = 0;
        } else if (!strcmp(line, "key")) {
            press(atoi(a));
        } else if (!strcmp(line, "shot")) {
            shot(a);
        } else if (!strcmp(line, "lcd")) {                   // lcd FILE: what the LCD shows (RefLCD)
            lcdshot(a);
        } else if (!strcmp(line, "msg")) {
            for (int y = 0; y < 16; y++) { for (int x = 0; x < 131; x++) putchar(lcd[y][x] ? '#' : ' '); putchar('\n'); }
        } else if (!strcmp(line, "export")) {
            int *idx = (int *) malloc(sizeof(int) * prgms_count);
            for (int i = 0; i < prgms_count; i++) idx[i] = i;
            core_export_programs(prgms_count, idx, a);
            printf("exported %d programs to %s\n", prgms_count, a);
        } else if (!strcmp(line, "regs")) {                  // regs A B: print R(A) ... R(B)
            int r0, r1; sscanf(a, "%d %d", &r0, &r1);
            vartype *regs = recall_var("REGS", 4);
            for (int r = r0; r <= r1 && regs && regs->type == TYPE_REALMATRIX; r++) {
                vartype_realmatrix *rm = (vartype_realmatrix *) regs;
                if (rm->array->is_string[r]) { char *t; int4 n; get_matrix_string(rm, r, &t, &n); printf("R%02d %.*s\n", r, (int) n, t); }
                else printf("R%02d %g\n", r, (double) rm->array->data[r]);
            }
        } else if (!strcmp(line, "import")) {
            core_import_programs(0, a);
            printf("imported %s: %d programs\n", a, prgms_count);
        } else if (!strcmp(line, "stack")) {
            for (int i = sp; i >= 0 && i > sp - 4; i--) {
                vartype *v = stack[i]; char b[100]; int n = vartype2string(v, b, 99); b[n] = 0; printf("%c: %s\n", "XYZT"[sp - i], b);
            }
            printf("ALPHA: %.*s\n", reg_alpha_length, reg_alpha);
            printf("sp %d  prgm_mode %d  running %d  pc %d prgm %d\n", sp, flags.f.prgm_mode, program_running(), (int) pc, current_prgm);
        }
        fflush(stdout);
    }
    return 0;
}
