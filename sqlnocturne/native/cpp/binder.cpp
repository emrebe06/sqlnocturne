#include <sstream>
#include <string>
#include <vector>

namespace sqlnocturne {

std::string describe_bindings(const std::vector<std::string>& param_types) {
    std::ostringstream out;
    out << "bindings:";
    for (const std::string& item : param_types) {
        out << " " << item;
    }
    return out.str();
}

} // namespace sqlnocturne
