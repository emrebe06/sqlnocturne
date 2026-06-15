pub fn tokenize(sql: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    let mut quote: Option<char> = None;
    for ch in sql.chars() {
        if let Some(q) = quote {
            current.push(ch);
            if ch == q {
                tokens.push(current.clone());
                current.clear();
                quote = None;
            }
            continue;
        }
        if ch == '\'' || ch == '"' {
            if !current.is_empty() {
                tokens.push(current.to_ascii_uppercase());
                current.clear();
            }
            current.push(ch);
            quote = Some(ch);
        } else if ch.is_ascii_alphanumeric() || ch == '_' || ch == '*' {
            current.push(ch);
        } else {
            if !current.is_empty() {
                tokens.push(current.to_ascii_uppercase());
                current.clear();
            }
            if matches!(ch, ';' | '(' | ')' | ',' | '=') {
                tokens.push(ch.to_string());
            }
        }
    }
    if !current.is_empty() {
        tokens.push(current.to_ascii_uppercase());
    }
    tokens
}
