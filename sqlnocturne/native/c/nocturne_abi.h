#ifndef NOCTURNE_ABI_H
#define NOCTURNE_ABI_H

#include <stddef.h>
#include "nocturne_scan.h"

#ifdef _WIN32
  #ifdef NOCTURNE_BUILD
    #define NOCTURNE_EXPORT __declspec(dllexport)
  #else
    #define NOCTURNE_EXPORT __declspec(dllimport)
  #endif
#else
  #define NOCTURNE_EXPORT
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct nocturne_result {
    int ok;
    int code;
    double risk_score;
    const char* message;
} nocturne_result;

/*
Future C ABI bridge for SQLNocturne.

Planned functions:
- nocturne_validate_query
- nocturne_format_result
- nocturne_bind_params
- nocturne_plan_cache_get
- nocturne_plan_cache_put

V0.1 keeps native code optional. Python must work without compiling this file.
*/

NOCTURNE_EXPORT const char* nocturne_version(void);
NOCTURNE_EXPORT nocturne_result nocturne_validate_query(const char* sql);
NOCTURNE_EXPORT const char* nocturne_validate_query_json(const char* sql, const char* mode);
NOCTURNE_EXPORT void nocturne_free_string(const char* value);
NOCTURNE_EXPORT const char* nocturne_runtime_json(void);

#ifdef __cplusplus
}
#endif

#endif
