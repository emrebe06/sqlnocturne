#ifndef SQLNOCTURNE_SCAN_H
#define SQLNOCTURNE_SCAN_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

enum {
    NOCTURNE_SCAN_EMPTY = 1u << 0,
    NOCTURNE_SCAN_MULTI_STATEMENT = 1u << 1,
    NOCTURNE_SCAN_DELETE_NO_WHERE = 1u << 2,
    NOCTURNE_SCAN_UPDATE_NO_WHERE = 1u << 3,
    NOCTURNE_SCAN_SELECT_STAR_NO_LIMIT = 1u << 4,
    NOCTURNE_SCAN_UNION_SELECT = 1u << 5,
    NOCTURNE_SCAN_TAUTOLOGY = 1u << 6,
    NOCTURNE_SCAN_COMMENT = 1u << 7,
    NOCTURNE_SCAN_DANGEROUS_SCHEMA = 1u << 8,
    NOCTURNE_SCAN_TIME_PROBE = 1u << 9,
    NOCTURNE_SCAN_UNBALANCED_QUOTE = 1u << 10,
    NOCTURNE_SCAN_INFORMATION_SCHEMA = 1u << 11
};

typedef struct nocturne_scan_report {
    int allowed;
    unsigned int flags;
    double risk_score;
    const char* code;
    const char* message;
} nocturne_scan_report;

nocturne_scan_report nocturne_scan_sql(const char* sql, size_t sql_size, const char* mode);
const char* nocturne_scan_report_json(nocturne_scan_report report);

#ifdef __cplusplus
}
#endif

#endif
