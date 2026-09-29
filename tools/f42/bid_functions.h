#pragma once
#include <stdlib.h>
#include <string.h>
typedef unsigned long long BID_UINT64;
typedef struct { BID_UINT64 w[2]; } BID_UINT128;
static inline void bid128_from_string(BID_UINT128 *r, char *s) { double d = strtod(s, 0); memset(r, 0, sizeof *r); memcpy(r, &d, sizeof d); }
static inline void bid128_to_binary64(double *d, BID_UINT128 *r) { memcpy(d, r, sizeof *d); }
static inline void bid64_to_binary64(double *d, BID_UINT64 *r) { memcpy(d, r, sizeof *d); }
static inline void binary64_to_bid128(BID_UINT128 *r, double *d) { memset(r, 0, sizeof *r); memcpy(r, d, sizeof *d); }
#include <stdio.h>
static inline void bid128_to_string(char *s, BID_UINT128 *r) {
    double d; memcpy(&d, r, sizeof d);
    snprintf(s, 50, "%.15e", d); double d2 = strtod(s, 0);
    if (d2 != d) snprintf(s, 50, "%.16e", d);
}
static inline void bid128_isZero(int *res, BID_UINT128 *r) { double d; memcpy(&d, r, sizeof d); *res = d == 0; }
static inline void bid128_isSigned(int *res, BID_UINT128 *r) { double d; memcpy(&d, r, sizeof d); *res = d < 0 || (d == 0 && 1 / d < 0); }
static inline void bid128_to_binary128(BID_UINT128 *out, BID_UINT128 *in) { memset(out, 0, sizeof *out); }
typedef unsigned int BID_UINT32;
static inline void binary64_to_bid32(BID_UINT32 *r, double *d) { *r = 0; }
static inline void binary64_to_bid64(BID_UINT64 *r, double *d) { memcpy(r, d, sizeof *d); }
static inline void bid32_to_binary64(double *d, BID_UINT32 *r) { *d = 0; }
static inline void bid128_from_int32(BID_UINT128 *r, int *i) { double d = *i; binary64_to_bid128(r, &d); }
static inline void bid128_to_bid32(BID_UINT32 *r, BID_UINT128 *a) { *r = 0; }
static inline void bid128_to_bid64(BID_UINT64 *r, BID_UINT128 *a) { *r = a->w[0]; }
static inline void bid128_to_binary32(float *f, BID_UINT128 *a) { double d; memcpy(&d, a, 8); *f = (float) d; }
static inline void bid32_to_bid128(BID_UINT128 *r, BID_UINT32 *a) { memset(r, 0, sizeof *r); }
static inline void bid64_to_bid128(BID_UINT128 *r, BID_UINT64 *a) { memset(r, 0, sizeof *r); r->w[0] = *a; }
static inline void binary128_to_bid128(BID_UINT128 *r, BID_UINT128 *a) { memset(r, 0, sizeof *r); }
static inline void binary32_to_bid128(BID_UINT128 *r, float *f) { double d = *f; binary64_to_bid128(r, &d); }
