#include "nocturne_alloc.h"

#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <malloc.h>
#endif

static nocturne_alloc_stats g_stats = {0, 0, 0, 0, 0};

static int nocturne_is_power_of_two(size_t value) {
    return value != 0 && (value & (value - 1)) == 0;
}

nocturne_platform nocturne_current_platform(void) {
#if defined(_WIN32)
    return NOCTURNE_PLATFORM_WINDOWS;
#elif defined(__APPLE__)
    return NOCTURNE_PLATFORM_APPLE;
#elif defined(__ANDROID__)
    return NOCTURNE_PLATFORM_ANDROID;
#elif defined(__linux__)
    return NOCTURNE_PLATFORM_LINUX;
#elif defined(__unix__)
    return NOCTURNE_PLATFORM_POSIX;
#else
    return NOCTURNE_PLATFORM_UNKNOWN;
#endif
}

const char* nocturne_platform_name(nocturne_platform platform) {
    switch (platform) {
    case NOCTURNE_PLATFORM_WINDOWS: return "windows";
    case NOCTURNE_PLATFORM_APPLE: return "apple";
    case NOCTURNE_PLATFORM_ANDROID: return "android";
    case NOCTURNE_PLATFORM_LINUX: return "linux";
    case NOCTURNE_PLATFORM_POSIX: return "posix";
    default: return "unknown";
    }
}

size_t nocturne_normalize_alignment(size_t alignment) {
    size_t pointer = sizeof(void*);
    size_t value = alignment == 0 ? pointer : alignment;
    if (value < pointer) value = pointer;
    if (nocturne_is_power_of_two(value)) return value;
    size_t power = pointer;
    while (power < value) {
        if (power > ((size_t)-1 / 2)) return pointer;
        power <<= 1;
    }
    return power;
}

void* nocturne_alloc(size_t size, size_t alignment) {
    if (size == 0) return 0;
    alignment = nocturne_normalize_alignment(alignment);
#if defined(_WIN32)
    void* ptr = _aligned_malloc(size, alignment);
#elif defined(__APPLE__) || defined(__ANDROID__) || defined(__linux__) || defined(__unix__)
    void* ptr = 0;
    if (posix_memalign(&ptr, alignment, size) != 0) ptr = 0;
#else
    void* raw = malloc(size + alignment + sizeof(void*));
    void* ptr = 0;
    if (raw) {
        size_t start = (size_t)raw + sizeof(void*);
        size_t aligned = (start + alignment - 1) & ~(alignment - 1);
        ((void**)aligned)[-1] = raw;
        ptr = (void*)aligned;
    }
#endif
    if (ptr) {
        g_stats.allocations += 1;
        g_stats.bytes_allocated += size;
        size_t active = g_stats.bytes_allocated - g_stats.bytes_freed;
        if (active > g_stats.high_watermark) g_stats.high_watermark = active;
    }
    return ptr;
}

void* nocturne_realloc(void* ptr, size_t old_size, size_t new_size, size_t alignment) {
    if (!ptr) return nocturne_alloc(new_size, alignment);
    if (new_size == 0) {
        nocturne_free(ptr, old_size);
        return 0;
    }
    void* next = nocturne_alloc(new_size, alignment);
    if (!next) return 0;
    memcpy(next, ptr, old_size < new_size ? old_size : new_size);
    nocturne_free(ptr, old_size);
    return next;
}

void nocturne_free(void* ptr, size_t size) {
    if (!ptr) return;
#if defined(_WIN32)
    _aligned_free(ptr);
#elif defined(__APPLE__) || defined(__ANDROID__) || defined(__linux__) || defined(__unix__)
    free(ptr);
#else
    free(((void**)ptr)[-1]);
#endif
    g_stats.frees += 1;
    g_stats.bytes_freed += size;
}

char* nocturne_strdup(const char* value) {
    if (!value) return 0;
    size_t length = strlen(value);
    char* out = (char*)nocturne_alloc(length + 1, sizeof(char));
    if (!out) return 0;
    memcpy(out, value, length + 1);
    return out;
}

nocturne_alloc_stats nocturne_allocator_stats(void) {
    return g_stats;
}
