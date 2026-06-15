#include "engine.hpp"

#include <mutex>
#include <string>
#include <unordered_map>

namespace sqlnocturne {

class PlanCache {
public:
    void put(const std::string& key, const NativePlan& plan) {
        std::lock_guard<std::mutex> lock(mutex_);
        plans_[key] = plan;
    }

    bool get(const std::string& key, NativePlan& out) const {
        std::lock_guard<std::mutex> lock(mutex_);
        auto found = plans_.find(key);
        if (found == plans_.end()) {
            return false;
        }
        out = found->second;
        return true;
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return plans_.size();
    }

private:
    mutable std::mutex mutex_;
    std::unordered_map<std::string, NativePlan> plans_;
};

} // namespace sqlnocturne
