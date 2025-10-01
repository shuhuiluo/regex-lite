from regex_lite.matcher import replace

def test_replace_basic():
    # Simple replacement
    result, count = replace(r"\d+", "", "abc 123 xyz 456", "#")
    assert result == "abc # xyz #"
    assert count == 2
    
    # No matches
    result, count = replace(r"\d+", "", "abc xyz", "#")
    assert result == "abc xyz"
    assert count == 0
    
    # Case insensitive
    result, count = replace("abc", "i", "ABC def ABC", "X")
    assert result == "X def X"
    assert count == 2


# def test_replace_debug_detailed():
#     from regex_lite.matcher import match_spans
    
#     text = "abc 123 xyz 456"
#     pattern = r"\d+"
#     repl = "#"
    
#     spans = match_spans(pattern, text, "")
#     print(f"Original text: {text!r} (len={len(text)})")
#     print(f"Spans found: {spans}")
    
#     # Manually trace the replacement
#     result = text
#     for i, (start, end) in enumerate(reversed(spans)):
#         print(f"\nStep {i+1}: Replacing span ({start}, {end})")
#         print(f"  Before: {result!r}")
#         print(f"  Extracted match: {result[start:end]!r}")
#         print(f"  result[:start] = {result[:start]!r}")
#         print(f"  repl = {repl!r}")
#         print(f"  result[end:] = {result[end:]!r}")
#         result = result[:start] + repl + result[end:]
#         print(f"  After: {result!r}")
    
    print(f"\nFinal result: {result!r}")