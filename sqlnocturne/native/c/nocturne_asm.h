#ifndef SQLNOCTURNE_ASM_H
#define SQLNOCTURNE_ASM_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

uint64_t nocturne_cpu_cycles(void);
const char* nocturne_asm_backend(void);

#ifdef __cplusplus
}
#endif

#endif
