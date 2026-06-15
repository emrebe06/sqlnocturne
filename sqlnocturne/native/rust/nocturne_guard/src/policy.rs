#[derive(Debug, Clone)]
pub struct PolicyDecision {
    pub allowed: bool,
    pub reason: Option<String>,
}

pub fn allow() -> PolicyDecision {
    PolicyDecision {
        allowed: true,
        reason: None,
    }
}

pub fn decide(report: &crate::risk::RiskReport) -> PolicyDecision {
    if report.allowed {
        return allow();
    }
    PolicyDecision {
        allowed: false,
        reason: report.reasons.first().cloned(),
    }
}
