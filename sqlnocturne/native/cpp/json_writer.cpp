#include <sstream>
#include <string>

namespace sqlnocturne {

static std::string escape_json(const std::string& value) {
    std::ostringstream out;
    for (char ch : value) {
        if (ch == '\\') {
            out << "\\\\";
        } else if (ch == '"') {
            out << "\\\"";
        } else if (ch == '\n') {
            out << "\\n";
        } else {
            out << ch;
        }
    }
    return out.str();
}

std::string write_status_json(bool ok, const std::string& code, const std::string& message) {
    std::ostringstream out;
    out << "{";
    out << "\"ok\":" << (ok ? "true" : "false") << ",";
    out << "\"code\":\"" << escape_json(code) << "\",";
    out << "\"message\":\"" << escape_json(message) << "\"";
    out << "}";
    return out.str();
}

} // namespace sqlnocturne
