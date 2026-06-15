#include "nocturne_asm.h"

#if defined(_MSC_VER) && (defined(_M_X64) || defined(_M_IX86))
#include <intrin.h>
#endif

uint64_t nocturne_cpu_cycles(void) {
#if defined(_MSC_VER) && (defined(_M_X64) || defined(_M_IX86))
    return __rdtsc();
#elif defined(__i386__) || defined(__x86_64__)
    unsigned int lo = 0;
    unsigned int hi = 0;
    __asm__ __volatile__("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
#elif defined(__aarch64__) && defined(__GNUC__)
    uint64_t value = 0;
    __asm__ __volatile__("mrs %0, cntvct_el0" : "=r"(value));
    return value;
#else
    return 0;
#endif
}

const char* nocturne_asm_backend(void) {
#if defined(_MSC_VER) && (defined(_M_X64) || defined(_M_IX86))
    return "msvc_rdtsc";
#elif defined(__i386__) || defined(__x86_64__)
    return "inline_x86_rdtsc";
#elif defined(__aarch64__) && defined(__GNUC__)
    return "inline_arm64_cntvct";
#else
    return "none";
#endif
}
