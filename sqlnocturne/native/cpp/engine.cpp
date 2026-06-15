#include "engine.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>

namespace sqlnocturne {

namespace {
std::string upper(std::string value) {
    std::transform(value.begin(), value.end(), value.begin(), [](unsigned char ch) {
        return static_cast<char>(std::toupper(ch));
    });
    return value;
}

bool contains(const std::string& text, const std::string& token) {
    return upper(text).find(upper(token)) != std::string::npos;
}

std::string first_keyword(const std::string& sql) {
    for (size_t i = 0; i < sql.size(); ++i) {
        if (!std::isalpha(static_cast<unsigned char>(sql[i]))) continue;
        size_t start = i;
        while (i < sql.size() && (std::isalnum(static_cast<unsigned char>(sql[i])) || sql[i] == '_')) ++i;
        return upper(sql.substr(start, i - start));
    }
    return "RAW";
}

std::string escape_json(const std::string& value) {
    std::ostringstream out;
    for (char ch : value) {
        if (ch == '\\') out << "\\\\";
        else if (ch == '"') out << "\\\"";
        else if (ch == '\n') out << "\\n";
        else out << ch;
    }
    return out.str();
}
}

std::string Engine::version() const {
    return "0.1.0";
}

NativePlan Engine::prepare(const std::string& sql) const {
    NativePlan plan;
    plan.sql = sql;
    plan.query_type = first_keyword(sql);
    plan.risk_score = sql.empty() ? 0.82 : 0.02;
    if (sql.empty()) {
        plan.allowed = false;
        plan.warnings.push_back("empty_sql");
    }
    if ((plan.query_type == "DELETE" || plan.query_type == "UPDATE") && !contains(sql, "WHERE")) {
        plan.allowed = false;
        plan.risk_score = plan.query_type == "DELETE" ? 0.98 : 0.94;
        plan.warnings.push_back(plan.query_type == "DELETE" ? "delete_without_where" : "update_without_where");
    }
    if (plan.query_type == "SELECT" && contains(sql, "SELECT *") && !contains(sql, "LIMIT")) {
        plan.risk_score = std::max(plan.risk_score, 0.32);
        plan.warnings.push_back("select_star_without_limit");
    }
    if (contains(sql, "UNION SELECT") || contains(sql, " OR 1=1") || contains(sql, " OR TRUE")) {
        plan.risk_score = std::max(plan.risk_score, 0.86);
        plan.allowed = false;
        plan.cacheable = false;
        plan.warnings.push_back("injection_shape");
    }
    return plan;
}

std::string Engine::prepare_json(const std::string& sql) const {
    NativePlan plan = prepare(sql);
    std::ostringstream out;
    out << "{";
    out << "\"allowed\":" << (plan.allowed ? "true" : "false") << ",";
    out << "\"cacheable\":" << (plan.cacheable ? "true" : "false") << ",";
    out << "\"query_type\":\"" << escape_json(plan.query_type) << "\",";
    out << "\"risk_score\":" << plan.risk_score << ",";
    out << "\"warnings\":[";
    for (size_t i = 0; i < plan.warnings.size(); ++i) {
        if (i) out << ",";
        out << "\"" << escape_json(plan.warnings[i]) << "\"";
    }
    out << "]}";
    return out.str();
}

} // namespace sqlnocturne
