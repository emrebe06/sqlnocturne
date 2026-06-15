#[derive(Debug, Clone)]
pub struct RiskReport {
    pub allowed: bool,
    pub score: f64,
    pub reasons: Vec<String>,
}

pub fn score_tokens(tokens: &[String]) -> RiskReport {
    let mut score = 0.02;
    let mut reasons = Vec::new();
    if tokens.contains(&"DELETE".to_string()) && !tokens.contains(&"WHERE".to_string()) {
        score = 0.98;
        reasons.push("DELETE_WITHOUT_WHERE".to_string());
    }
    if tokens.contains(&"UPDATE".to_string()) && !tokens.contains(&"WHERE".to_string()) {
        score = score.max(0.94);
        reasons.push("UPDATE_WITHOUT_WHERE".to_string());
    }
    if tokens.contains(&"SELECT".to_string()) && tokens.contains(&"*".to_string()) && !tokens.contains(&"LIMIT".to_string()) {
        score = score.max(0.32);
        reasons.push("SELECT_STAR_WITHOUT_LIMIT".to_string());
    }
    if has_phrase(tokens, &["UNION", "SELECT"]) {
        score = score.max(0.82);
        reasons.push("UNION_SELECT".to_string());
    }
    if has_phrase(tokens, &["OR", "1", "=", "1"]) || has_phrase(tokens, &["OR", "TRUE"]) {
        score = score.max(0.88);
        reasons.push("TAUTOLOGY".to_string());
    }
    if tokens.contains(&"DROP".to_string()) || tokens.contains(&"TRUNCATE".to_string()) || tokens.contains(&"ALTER".to_string()) {
        score = score.max(0.86);
        reasons.push("DANGEROUS_SCHEMA_OPERATION".to_string());
    }
    RiskReport {
        allowed: score < 0.80,
        score,
        reasons,
    }
}

fn has_phrase(tokens: &[String], phrase: &[&str]) -> bool {
    if phrase.is_empty() || tokens.len() < phrase.len() {
        return false;
    }
    tokens.windows(phrase.len()).any(|window| {
        window
            .iter()
            .zip(phrase.iter())
            .all(|(left, right)| left == right)
    })
}
