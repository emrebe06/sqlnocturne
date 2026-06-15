#include "nocturne_abi.h"
#include "nocturne_alloc.h"
#include "nocturne_asm.h"

#include <stdio.h>
#include <string.h>

const char* nocturne_version(void) {
    return "0.1.0";
}

nocturne_result nocturne_validate_query(const char* sql) {
    nocturne_result result;
    nocturne_scan_report report = nocturne_scan_sql(sql, sql ? strlen(sql) : 0, "strict");
    result.ok = report.allowed;
    result.code = report.allowed ? 0 : 1;
    result.risk_score = report.risk_score;
    result.message = report.message;
    return result;
}

const char* nocturne_validate_query_json(const char* sql, const char* mode) {
    nocturne_scan_report report = nocturne_scan_sql(sql, sql ? strlen(sql) : 0, mode ? mode : "strict");
    return nocturne_scan_report_json(report);
}

void nocturne_free_string(const char* value) {
    nocturne_free((void*)value, value ? strlen(value) + 1 : 0);
}

const char* nocturne_runtime_json(void) {
    nocturne_alloc_stats stats = nocturne_allocator_stats();
    char buffer[512];
    snprintf(
        buffer,
        sizeof(buffer),
        "{\"version\":\"%s\",\"platform\":\"%s\",\"asm\":\"%s\",\"cycles\":%llu,\"allocations\":%llu,\"frees\":%llu,\"high_watermark\":%llu}",
        nocturne_version(),
        nocturne_platform_name(nocturne_current_platform()),
        nocturne_asm_backend(),
        (unsigned long long)nocturne_cpu_cycles(),
        (unsigned long long)stats.allocations,
        (unsigned long long)stats.frees,
        (unsigned long long)stats.high_watermark
    );
    return nocturne_strdup(buffer);
}
