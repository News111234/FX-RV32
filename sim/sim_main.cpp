#include <verilated.h>
#include "Vcore_top_sim.h"

vluint64_t main_time = 0;
const vluint64_t sim_limit = 30000000000; // 30 second timeout (ns)

double sc_time_stamp() { return main_time; }

int main(int argc, char** argv) {
    Verilated::commandArgs(argc, argv);
    Vcore_top_sim* top = new Vcore_top_sim("top");

    top->clk_i = 0;
    top->rst_n_i = 0;

    while (!Verilated::gotFinish() && main_time < sim_limit) {
        top->clk_i = !top->clk_i;

        if (main_time < 100) top->rst_n_i = 0;
        else top->rst_n_i = 1;

        top->eval();

        // Check for tohost-based test completion (riscv-tests)
        if (top->tohost_done) {
            if (top->tohost_pass) {
                printf("\n=== TEST PASSED at time %lu ns ===\n", (unsigned long)main_time);
            } else {
                printf("\n=== TEST FAILED at time %lu ns ===\n", (unsigned long)main_time);
            }
            break;
        }

        // Check for CoreMark completion
        if (top->perf_score != 0) {
            printf("\nCoreMark completed at time %lu ns\n", (unsigned long)main_time);
            printf("total_time(ms)   = %u\n", top->perf_total_time);
            printf("score            = %u\n", top->perf_score);
            printf("iterations       = %u\n", top->perf_iterations);
            printf("data_size(bytes) = %u\n", top->perf_data_size);
            printf("seedcrc(hex)     = 0x%x\n", top->perf_seedcrc);
            printf("total_errors     = %u\n", top->perf_total_errors);
            break;
        }

        if (main_time % 1000000 == 0) {
            printf("Time: %lu ns, pc=%08x\n", (unsigned long)main_time, top->debug_if_pc);
        }

        main_time += 5;
    }

    if (main_time >= sim_limit) {
        printf("Simulation timeout reached.\n");
    }

    delete top;
    return 0;
}
