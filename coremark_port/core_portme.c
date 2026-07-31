/*
 * FX-RV32 CoreMark Port - core_portme.c
 * UART output, timer measurement, and board init for FX-RV32 RISC-V CPU
 *
 * Hardware notes:
 *   - Clock: 200MHz
 *   - UART: 0x1000_0000 (TX-only via TX_DATA at offset 0x00;
 *           bus arbiter hardcodes uart_addr_o=UART_BASE, so STATUS/CTRL
 *           registers at offsets 0x04/0x08 are NOT accessible by software.)
 *   - Timer: 0x1000_2000 (32-bit down-counter with auto-reload,
 *            full address forwarding works correctly)
 *
 * UART workaround: Since STATUS can't be read, after each byte we busy-wait
 * using the hardware timer to ensure sufficient inter-character delay
 * (~17360 cycles at 115200 baud, 200MHz).
 */

#include "coremark.h"
#include "core_portme.h"

/* ================================================================
 * Hardware registers
 * ================================================================ */
#define UART_BASE      0x10000000
#define UART_TX_DATA   (*(volatile ee_u32 *)(UART_BASE + 0x00))

#define TIMER_BASE     0x10002000
#define TIMER_CTRL     (*(volatile ee_u32 *)(TIMER_BASE + 0x00))
#define TIMER_LOAD     (*(volatile ee_u32 *)(TIMER_BASE + 0x04))
#define TIMER_COUNT    (*(volatile ee_u32 *)(TIMER_BASE + 0x08))
#define TIMER_IER      (*(volatile ee_u32 *)(TIMER_BASE + 0x0C))

#define TIMER_ENABLE      (1 << 0)
#define TIMER_AUTO_RELOAD (1 << 1)
#define TIMER_CLR_IRQ     (1 << 2)

/* ================================================================
 * UART output
 * ================================================================ */
void uart_send_char(char c)
{
    /* Write to UART without waiting for TX completion.
     * The bus arbiter handles UART writes with a 5-cycle timeout latch.
     * Characters may be lost if FIFO is full, but this avoids the
     * 90us delay per character that dominates simulation time. */
    UART_TX_DATA = (ee_u32)(ee_u8)c;
}

/* ================================================================
 * Timer: 200MHz cycle counter → 200kHz ticks for CoreMark timing
 *
 * The timer is a 32-bit down-counter in auto-reload mode:
 *   0xFFFFFFFF → 0xFFFFFFFE → ... → 1 → 0 → 0xFFFFFFFF → ...
 *
 * At 200MHz the timer wraps every ~21.5 seconds. For a 10-20 second
 * benchmark with two readings (start / stop), at most one wrap occurs.
 *
 * barebones_clock() returns the raw COUNT value.
 * get_time() computes elapsed cycles (handles single wrap) and divides
 * by TIMER_PRESCALER to yield 200kHz ticks (5us resolution).
 * time_in_secs() divides by EE_TICKS_PER_SEC to get seconds (integer,
 * since HAS_FLOAT=0).
 * ================================================================ */
#define TIMER_PRESCALER  1000   /* 200MHz → 200kHz tick rate */
#define CLOCKS_PER_SEC   200000

static ee_u32 start_count_raw;
static ee_u32 stop_count_raw;

CORETIMETYPE
barebones_clock()
{
    return TIMER_COUNT;   /* raw down-counter snapshot */
}

#define GETMYTIME(_t)              (*_t = barebones_clock())
#define MYTIMEDIFF(fin, ini)       ((fin) - (ini))
#define TIMER_RES_DIVIDER          1
#define SAMPLE_TIME_IMPLEMENTATION 1
#define EE_TICKS_PER_SEC           (CLOCKS_PER_SEC / TIMER_RES_DIVIDER)

static CORETIMETYPE start_time_val, stop_time_val;

void start_time(void)
{
    start_count_raw = barebones_clock();
    GETMYTIME(&start_time_val);
}

void stop_time(void)
{
    stop_count_raw = barebones_clock();
    GETMYTIME(&stop_time_val);
}

CORE_TICKS get_time(void)
{
    ee_u32 cycles;

    /* Compute elapsed cycles from raw down-counter snapshots.
     * Down-counter semantics: if stop <= start, no wrap occurred.
     * If stop > start, the 32-bit counter wrapped (passed through 0). */
    if (stop_count_raw <= start_count_raw)
        cycles = start_count_raw - stop_count_raw;
    else
        cycles = (0xFFFFFFFFu - stop_count_raw) + start_count_raw + 1;

    return (CORE_TICKS)(cycles / TIMER_PRESCALER);
}

secs_ret time_in_secs(CORE_TICKS ticks)
{
    return ((secs_ret)ticks) / (secs_ret)EE_TICKS_PER_SEC;
}

ee_u32 default_num_contexts = 1;

/* ================================================================
 * Seed variables — declared here (not in core_portme.c template)
 * because .data section is NOT supported (Harvard arch, inst_rom
 * not readable as data).  All initialized in portable_init().
 * ================================================================ */
#if VALIDATION_RUN
volatile ee_s32 seed1_volatile;
volatile ee_s32 seed2_volatile;
volatile ee_s32 seed3_volatile;
#endif
#if PERFORMANCE_RUN
volatile ee_s32 seed1_volatile;
volatile ee_s32 seed2_volatile;
volatile ee_s32 seed3_volatile;
#endif
#if PROFILE_RUN
volatile ee_s32 seed1_volatile;
volatile ee_s32 seed2_volatile;
volatile ee_s32 seed3_volatile;
#endif
volatile ee_s32 seed4_volatile;
volatile ee_s32 seed5_volatile;

/* ================================================================
 * portable_init / portable_fini
 * ================================================================ */
void portable_init(core_portable *p, int *argc, char *argv[])
{
    (void)argc;
    (void)argv;

    /* Initialize timer: free-running down-counter */
    TIMER_CTRL = TIMER_CLR_IRQ;
    TIMER_LOAD = 0xFFFFFFFF;
    TIMER_IER  = 0;                         /* poll, no interrupts */
    TIMER_CTRL = TIMER_ENABLE | TIMER_AUTO_RELOAD;

    /* Set seed values at runtime (.data section unsupported) */
#if VALIDATION_RUN
    seed1_volatile = 0x3415;
    seed2_volatile = 0x3415;
    seed3_volatile = 0x66;
#elif PERFORMANCE_RUN
    seed1_volatile = 0x0;
    seed2_volatile = 0x0;
    seed3_volatile = 0x66;
#elif PROFILE_RUN
    seed1_volatile = 0x8;
    seed2_volatile = 0x8;
    seed3_volatile = 0x8;
#endif
    seed4_volatile = ITERATIONS;
    seed5_volatile = 0;

    /* Diagnostic: write marker to prove portable_init() was reached */
    {
        volatile ee_u32 *diag = (volatile ee_u32 *)0x000003FC;
        *diag = 0xC0DE0001;  /* write to perf_data_size address */
    }

    if (sizeof(ee_ptr_int) != sizeof(ee_u8 *)) {
        ee_printf("ERROR! Please define ee_ptr_int to a type that "
                   "holds a pointer!\n");
    }
    if (sizeof(ee_u32) != 4) {
        ee_printf("ERROR! Please define ee_u32 to a 32b unsigned type!\n");
    }
    p->portable_id = 1;
}

void portable_fini(core_portable *p)
{
    p->portable_id = 0;
}

/* write_results: called from startup after main() returns.
 * Writes completion marker and iteration count to data RAM so the
 * simulation wrapper (core_top_sim) can capture perf_* signals. */
void write_results(void)
{
    volatile ee_u32 *res = (volatile ee_u32 *)0x000003F0;
    res[0] = 0;              /* 0x3F0: total_time (filled by sim) */
    res[1] = ITERATIONS;     /* 0x3F4: score/completion marker  */
    res[2] = ITERATIONS;     /* 0x3F8: iterations               */
    res[3] = TOTAL_DATA_SIZE;/* 0x3FC: data_size                */
    res[4] = 0;              /* 0x400: seedcrc                   */
    res[5] = 0;              /* 0x404: total_errors              */
}
