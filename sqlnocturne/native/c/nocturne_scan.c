#include "nocturne_scan.h"
#include "nocturne_alloc.h"

#include <ctype.h>
#include <stdio.h>
#include <string.h>

static int streq_ci(const char* a, const char* b) {
    if (!a || !b) return 0;
    while (*a && *b) {
        if (toupper((unsigned char)*a) != toupper((unsigned char)*b)) return 0;
        ++a;
        ++b;
    }
    return *a == 0 && *b == 0;
}

static int contains_ci(const char* text, const char* needle) {
    if (!text || !needle || !*needle) return 0;
    size_t n = strlen(needle);
    for (const char* p = text; *p; ++p) {
        size_t i = 0;
        while (i < n && p[i] && toupper((unsigned char)p[i]) == toupper((unsigned char)needle[i])) ++i;
        if (i == n) return 1;
    }
    return 0;
}

static int first_keyword(const char* sql, char* out, size_t out_size) {
    if (!sql || !out || out_size == 0) return 0;
    while (*sql && !isalpha((unsigned char)*sql)) ++sql;
    size_t i = 0;
    while (sql[i] && (isalnum((unsigned char)sql[i]) || sql[i] == '_') && i + 1 < out_size) {
        out[i] = (char)toupper((unsigned char)sql[i]);
        ++i;
    }
    out[i] = 0;
    return i > 0;
}

static int has_keyword(const char* sql, const char* keyword) {
    return contains_ci(sql, keyword);
}

static unsigned int count_semicolon_statements(const char* sql) {
    unsigned int statements = 0;
    int in_single = 0;
    int in_double = 0;
    int seen_text = 0;
    for (const char* p = sql; p && *p; ++p) {
        char ch = *p;
        if (ch == '\'' && !in_double) in_single = !in_single;
        else if (ch == '"' && !in_single) in_double = !in_double;
        else if (ch == ';' && !in_single && !in_double) {
            if (seen_text) {
                statements += 1;
                seen_text = 0;
            }
        } else if (!isspace((unsigned char)ch)) {
            seen_text = 1;
        }
    }
    if (seen_text) statements += 1;
    return statements;
}

static int has_unbalanced_quotes(const char* sql) {
    int single = 0;
    int dbl = 0;
    for (const char* p = sql; p && *p; ++p) {
        if (*p == '\'' && !dbl) single = !single;
        else if (*p == '"' && !single) dbl = !dbl;
    }
    return single || dbl;
}

static double risk_from_flags(unsigned int flags) {
    double score = 0.02;
    if (flags & NOCTURNE_SCAN_EMPTY) score += 0.80;
    if (flags & NOCTURNE_SCAN_MULTI_STATEMENT) score += 0.45;
    if (flags & NOCTURNE_SCAN_DELETE_NO_WHERE) score += 0.96;
    if (flags & NOCTURNE_SCAN_UPDATE_NO_WHERE) score += 0.92;
    if (flags & NOCTURNE_SCAN_SELECT_STAR_NO_LIMIT) score += 0.30;
    if (flags & NOCTURNE_SCAN_UNION_SELECT) score += 0.35;
    if (flags & NOCTURNE_SCAN_TAUTOLOGY) score += 0.50;
    if (flags & NOCTURNE_SCAN_COMMENT) score += 0.20;
    if (flags & NOCTURNE_SCAN_DANGEROUS_SCHEMA) score += 0.75;
    if (flags & NOCTURNE_SCAN_TIME_PROBE) score += 0.45;
    if (flags & NOCTURNE_SCAN_UNBALANCED_QUOTE) score += 0.24;
    if (flags & NOCTURNE_SCAN_INFORMATION_SCHEMA) score += 0.20;
    return score > 1.0 ? 1.0 : score;
}

nocturne_scan_report nocturne_scan_sql(const char* sql, size_t sql_size, const char* mode) {
    nocturne_scan_report report;
    report.allowed = 1;
    report.flags = 0;
    report.risk_score = 0.02;
    report.code = "OK";
    report.message = "SQL allowed";

    if (!sql || sql_size == 0 || !*sql) {
        report.allowed = 0;
        report.flags = NOCTURNE_SCAN_EMPTY;
        report.risk_score = 0.82;
        report.code = "EMPTY_SQL";
        report.message = "SQL cannot be empty";
        return report;
    }

    char qtype[32];
    qtype[0] = 0;
    first_keyword(sql, qtype, sizeof(qtype));

    if (count_semicolon_statements(sql) > 1) report.flags |= NOCTURNE_SCAN_MULTI_STATEMENT;
    if (streq_ci(qtype, "DELETE") && !has_keyword(sql, "WHERE")) report.flags |= NOCTURNE_SCAN_DELETE_NO_WHERE;
    if (streq_ci(qtype, "UPDATE") && !has_keyword(sql, "WHERE")) report.flags |= NOCTURNE_SCAN_UPDATE_NO_WHERE;
    if (streq_ci(qtype, "SELECT") && contains_ci(sql, "SELECT *") && !has_keyword(sql, "LIMIT")) report.flags |= NOCTURNE_SCAN_SELECT_STAR_NO_LIMIT;
    if (contains_ci(sql, "UNION SELECT")) report.flags |= NOCTURNE_SCAN_UNION_SELECT;
    if (contains_ci(sql, " OR 1=1") || contains_ci(sql, " OR TRUE")) report.flags |= NOCTURNE_SCAN_TAUTOLOGY;
    if (contains_ci(sql, "--") || contains_ci(sql, "/*")) report.flags |= NOCTURNE_SCAN_COMMENT;
    if (streq_ci(qtype, "DROP") || streq_ci(qtype, "TRUNCATE") || streq_ci(qtype, "ALTER")) report.flags |= NOCTURNE_SCAN_DANGEROUS_SCHEMA;
    if (contains_ci(sql, "SLEEP(") || contains_ci(sql, "BENCHMARK(")) report.flags |= NOCTURNE_SCAN_TIME_PROBE;
    if (has_unbalanced_quotes(sql)) report.flags |= NOCTURNE_SCAN_UNBALANCED_QUOTE;
    if (contains_ci(sql, "INFORMATION_SCHEMA")) report.flags |= NOCTURNE_SCAN_INFORMATION_SCHEMA;

    report.risk_score = risk_from_flags(report.flags);
    int strict = !mode || streq_ci(mode, "strict") || streq_ci(mode, "paranoid");
    if (strict && (report.flags & (NOCTURNE_SCAN_MULTI_STATEMENT | NOCTURNE_SCAN_DELETE_NO_WHERE | NOCTURNE_SCAN_UPDATE_NO_WHERE | NOCTURNE_SCAN_DANGEROUS_SCHEMA))) {
        report.allowed = 0;
    }
    if (strict && report.risk_score >= 0.85) report.allowed = 0;

    if (!report.allowed) {
        if (report.flags & NOCTURNE_SCAN_DELETE_NO_WHERE) {
            report.code = "DELETE_WITHOUT_WHERE";
            report.message = "DELETE without WHERE can remove an entire table";
        } else if (report.flags & NOCTURNE_SCAN_UPDATE_NO_WHERE) {
            report.code = "UPDATE_WITHOUT_WHERE";
            report.message = "UPDATE without WHERE can modify an entire table";
        } else if (report.flags & NOCTURNE_SCAN_MULTI_STATEMENT) {
            report.code = "MULTIPLE_STATEMENTS";
            report.message = "Multiple SQL statements are not allowed";
        } else {
            report.code = "SUSPICIOUS_SQL";
            report.message = "SQL contains dangerous native signals";
        }
    } else if (report.flags) {
        report.code = "WARNINGS";
        report.message = "SQL allowed with native warnings";
    }
    return report;
}

const char* nocturne_scan_report_json(nocturne_scan_report report) {
    char buffer[512];
    snprintf(
        buffer,
        sizeof(buffer),
        "{\"allowed\":%s,\"flags\":%u,\"risk_score\":%.4f,\"code\":\"%s\",\"message\":\"%s\"}",
        report.allowed ? "true" : "false",
        report.flags,
        report.risk_score,
        report.code ? report.code : "",
        report.message ? report.message : ""
    );
    return nocturne_strdup(buffer);
}
