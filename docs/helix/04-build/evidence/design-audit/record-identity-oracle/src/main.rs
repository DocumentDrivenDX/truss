//! Planned serializer byte oracle; not Truss/native implementation qualification.
use std::io::{self, Read};
use weft_core::ir::Identity;
fn hex(bytes: &[u8]) -> String { bytes.iter().map(|b| format!("{b:02x}")).collect() }
fn main() {
    let mut input = String::new(); io::stdin().read_to_string(&mut input).unwrap();
    let fixtures: serde_json::Value = serde_json::from_str(&input).unwrap();
    let cases = fixtures["cases"].as_array().unwrap();
    for case in cases {
        let identity: Identity = serde_json::from_value(case["identity"].clone()).unwrap();
        let actual = serde_json::json!(identity).to_string();
        assert_eq!(hex(actual.as_bytes()), case["expectedUtf8Hex"].as_str().unwrap(), "{}", case["id"]);
    }
    println!("{}", serde_json::json!({"cases":cases.len(),"scope":"Selected Identity/serde_json byte agreement only; not actual compiler build feature graph, native storage or Truss adoption"}));
}
