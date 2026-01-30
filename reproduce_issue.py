
import sys
import os

# Add current directory to path so we can import pipeline
sys.path.append(os.getcwd())

from pipeline.segmenter import Segmenter

# We need to monkey-patch or subclass to inspect the internal logic?
# Or just check the output.
# The `segment` method returns the merged list.
# If merged list has FEWER items than input, then a Merge happened.
# If "Chapter 1" content is inside "Part 1", we can check content.

def run_test(name, chapters):
    print(f"\n--- {name} ---")
    seg = Segmenter()
    # The real segmenter might look ahead and modify in place or return new list? 
    # It returns 'merged' list.
    
    result = seg.segment(chapters)
    
    for r in result:
        print(f"Title: {r['title']}")
        print(f"Content-Len: {len(r.get('content', ''))}")
        if len(r.get('content', '')) > 0:
            print(f"Preview: {r['content'][:50]}...")
            
    # Verification
    # If we started with 2 items and ended with 1, MERGE happened.
    # If we started with 2 items and ended with 2, SKIPPED MERGE.
    
    if len(result) < len(chapters):
        print("RESULT: MERGED (FAIL if unintended)")
    else:
        print("RESULT: SKIPPED MERGE (PASS)")

# Test Cases
print("Test 1: 'CHAPTER: 1: ...'")
chapters_1 = [
    {'title': "PART: The Fundamentals", 'content': "", 'level': 1, 'is_parent': True},
    {'title': "CHAPTER: 1: The Surprising Power", 'content': "Content...", 'level': 2, 'is_parent': False}
]
run_test("Test 1", chapters_1)

print("\nTest 2: '1. The Surprising Power...' (No 'Chapter' prefix)")
chapters_2 = [
    {'title': "PART: The Fundamentals", 'content': "", 'level': 1, 'is_parent': True},
    {'title': "1. The Surprising Power of Atomic Habits", 'content': "Content...", 'level': 2, 'is_parent': False}
]
run_test("Test 2", chapters_2)

print("\nTest 3: 'I. The Surprising Power...' (Roman)")
chapters_3 = [
    {'title': "PART: The Fundamentals", 'content': "", 'level': 1, 'is_parent': True},
    {'title': "I. The Surprising Power", 'content': "Content...", 'level': 2, 'is_parent': False}
]
run_test("Test 3", chapters_3)
