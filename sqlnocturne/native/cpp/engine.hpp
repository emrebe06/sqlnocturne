#ifndef SQLNOCTURNE_ENGINE_HPP
#define SQLNOCTURNE_ENGINE_HPP

#include <string>
#include <vector>

namespace sqlnocturne {

struct NativePlan {
    std::string sql;
    std::vector<std::string> param_types;
    std::vector<std::string> warnings;
    std::string query_type = "RAW";
    double risk_score = 0.02;
    bool cacheable = true;
    bool allowed = true;
};

class Engine {
public:
    std::string version() const;
    NativePlan prepare(const std::string& sql) const;
    std::string prepare_json(const std::string& sql) const;
};

} // namespace sqlnocturne

#endif
