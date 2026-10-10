#[test]
fn original_consumer_review() {
 let cases: serde_json::Value = serde_json::from_str(include_str!("../../../truss-consumer-frontend-inputs.json")).unwrap();
 let mut results = Vec::new();
 for case in cases.as_array().unwrap() {
  let result: serde_json::Value = serde_json::from_str(&weft_core::frontend_json(&case["request"].to_string())).unwrap();
  results.push(serde_json::json!({"source":case["source"],"variant":case["variant"],"response":result}));
 }
 std::fs::write("truss-consumer-frontend-results.json",serde_json::to_string_pretty(&results).unwrap()).unwrap();
}
