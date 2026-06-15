#ifndef SQLNOCTURNE_ALLOC_H
#define SQLNOCTURNE_ALLOC_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum nocturne_platform {
    NOCTURNE_PLATFORM_WINDOWS = 1,
    NOCTURNE_PLATFORM_APPLE = 2,
    NOCTURNE_PLATFORM_ANDROID = 3,
    NOCTURNE_PLATFORM_LINUX = 4,
    NOCTURNE_PLATFORM_POSIX = 5,
    NOCTURNE_PLATFORM_UNKNOWN = 99
} nocturne_platform;

typedef struct nocturne_alloc_stats {
    size_t allocations;
    size_t frees;
    size_t bytes_allocated;
    size_t bytes_freed;
    size_t high_watermark;
} nocturne_alloc_stats;

nocturne_platform nocturne_current_platform(void);
const char* nocturne_platform_name(nocturne_platform platform);
size_t nocturne_normalize_alignment(size_t alignment);
void* nocturne_alloc(size_t size, size_t alignment);
void* nocturne_realloc(void* ptr, size_t old_size, size_t new_size, size_t alignment);
void nocturne_free(void* ptr, size_t size);
char* nocturne_strdup(const char* value);
nocturne_alloc_stats nocturne_allocator_stats(void);

#ifdef __cplusplus
}
#endif

#endif
