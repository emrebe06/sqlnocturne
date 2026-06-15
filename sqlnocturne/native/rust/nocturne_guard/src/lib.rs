pub mod policy;
pub mod risk;
pub mod tokenizer;

pub fn version() -> &'static str {
    "0.1.0"
}

pub fn inspect(sql: &str) -> risk::RiskReport {
    let tokens = tokenizer::tokenize(sql);
    risk::score_tokens(&tokens)
}
