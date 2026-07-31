/*
 * FX-RV32 CoreMark Port - core_portme.h
 * RISC-V RV32I bare-metal port for FX-RV32 CPU
 * 200MHz, no FPU, no hardware mul/div
 */

#ifndef CORE_PORTME_H
#define CORE_PORTME_H

/* -------- Platform capabilities -------- */
#define HAS_FLOAT  0
#define HAS_TIME_H 0
#define USE_CLOCK  0
#define HAS_STDIO  0
#define HAS_PRINTF 0

/* -------- Compiler info -------- */
#ifndef COMPILER_VERSION
#ifdef __GNUC__
#define COMPILER_VERSION "GCC"__VERSION__
#else
#define COMPILER_VERSION "Unknown"
#endif
#endif
#ifndef COMPILER_FLAGS
#define COMPILER_FLAGS FLAGS_STR
#endif

#define MEM_LOCATION "STACK"

/* -------- Data types (RV32I ILP32) -------- */
typedef signed short   ee_s16;
typedef unsigned short ee_u16;
typedef signed int     ee_s32;
typedef double         ee_f32;    /* unused with HAS_FLOAT=0 */
typedef unsigned char  ee_u8;
typedef unsigned int   ee_u32;
typedef ee_u32         ee_ptr_int;
typedef unsigned int   ee_size_t;
#define NULL ((void *)0)

#define align_mem(x) (void *)(4 + (((ee_ptr_int)(x) - 1) & ~3))

/* -------- Timer -------- */
/* barebones_clock() returns elapsed time in 5us ticks (200kHz) */
#define CORETIMETYPE ee_u32
typedef ee_u32 CORE_TICKS;

/* -------- Seeds & memory -------- */
#define SEED_METHOD SEED_VOLATILE
#define MEM_METHOD  MEM_STATIC

/* -------- Single-threaded -------- */
#define MULTITHREAD       1
#define MAIN_HAS_NOARGC   1
#define MAIN_HAS_NORETURN 0

extern ee_u32 default_num_contexts;

typedef struct CORE_PORTABLE_S
{
    ee_u8 portable_id;
} core_portable;

void portable_init(core_portable *p, int *argc, char *argv[]);
void portable_fini(core_portable *p);

/* -------- Run type auto-detect -------- */
#if !defined(PROFILE_RUN) && !defined(PERFORMANCE_RUN) \
    && !defined(VALIDATION_RUN)
#if (TOTAL_DATA_SIZE == 1200)
#define PROFILE_RUN 1
#elif (TOTAL_DATA_SIZE == 2000)
#define PERFORMANCE_RUN 1
#else
#define VALIDATION_RUN 1
#endif
#endif

int ee_printf(const char *fmt, ...);

#endif /* CORE_PORTME_H */
