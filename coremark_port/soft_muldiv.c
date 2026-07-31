/*
 * Software integer multiply/divide for RV32I (no M extension).
 * These replace libgcc's hardware-mul/div versions.
 */

/* 32-bit unsigned division */
unsigned int __udivsi3(unsigned int num, unsigned int den)
{
    unsigned int quot = 0, bit = 1;

    if (den == 0) return 0;
    if (den > num) return 0;

    /* Align denominator with numerator */
    while (den <= num && !(den & (1u << 31))) {
        den <<= 1;
        bit <<= 1;
    }

    /* Long division */
    while (bit) {
        if (num >= den) {
            num -= den;
            quot |= bit;
        }
        den >>= 1;
        bit >>= 1;
    }
    return quot;
}

/* 32-bit unsigned modulo */
unsigned int __umodsi3(unsigned int num, unsigned int den)
{
    unsigned int quot = __udivsi3(num, den);
    return num - quot * den;
}

/* 32-bit signed division */
int __divsi3(int num, int den)
{
    int neg = 0;
    unsigned int uq;

    if (den == 0) return 0;
    if (num < 0) { num = -num; neg = !neg; }
    if (den < 0) { den = -den; neg = !neg; }

    uq = __udivsi3((unsigned)num, (unsigned)den);
    return neg ? -(int)uq : (int)uq;
}

/* 32-bit signed modulo */
int __modsi3(int num, int den)
{
    int q = __divsi3(num, den);
    return num - q * den;
}

/* 32-bit multiplication (shift-add) */
int __mulsi3(int a, int b)
{
    int res = 0;
    unsigned int ua = (unsigned int)a;
    unsigned int ub = (unsigned int)b;

    while (ub) {
        if (ub & 1) res += ua;
        ua <<= 1;
        ub >>= 1;
    }
    return res;
}
