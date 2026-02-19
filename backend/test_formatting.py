import requests
import json

def test_extraction():
    url = "http://127.0.0.1:8000/api/v1/semantic-scholar/extract-structured"
    # A sample PDF that is likely to have headers (Attention Is All You Need)
    payload = {
        "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"
    }
    
    print(f"Testing extraction from: {payload['pdf_url']}")
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            blocks = data.get("full_text", []) # Wait, the key might be different. Let me check the endpoint code.
            # In semantic_scholar.py:
            # return { "status": "success", "data": structured_blocks } ?? 
            # I need to check semantic_scholar.py response structure.
            
            # actually let's just print keys first
            print(f"Response Keys: {data.keys()}")
            
            if "blocks" in data:
                blocks = data["blocks"]
            elif "data" in data:
                blocks = data["data"]
            elif "full_text" in data and isinstance(data["full_text"], list):
                blocks = data["full_text"]
            else:
                 # It might be in 'full_text' if I mapped it that way, but let's check.
                 print("Could not find blocks list. printing first 500 chars of response:")
                 print(json.dumps(data, indent=2)[:500])
                 return

            print(f"\nExtracted {len(blocks)} blocks.")
            print("\n--- Block Structure Sample ---")
            
            counts = {"heading": 0, "subheading": 0, "body": 0}
            
            for i, block in enumerate(blocks):
                b_type = block.get("type", "unknown")
                if b_type in counts: counts[b_type] += 1
                
                # Print first few headers to verify detection
                if b_type in ["heading", "subheading"] or i < 5:
                    text_preview = block.get("text", "")[:50].replace("\n", " ")
                    print(f"[{b_type.upper()}] {text_preview}...")

                # Check for Figures/Tables specifically
                text_lower = block.get("text", "").strip().lower()
                if text_lower.startswith("figure") or text_lower.startswith("table"):
                    print(f"   -> Found Caption candidate: '{text_lower[:30]}...' -> Assigned Type: {b_type}")

                # Check for Garbage Headings (No letters, or just numbers)
                import re
                if b_type in ["heading", "subheading"]:
                    if not re.search(r'[a-zA-Z]', block.get("text", "")):
                        print(f"   -> [FAIL] Found Garbage Heading (No letters): '{block.get('text')}'")
                    if block.get("text", "").strip().isdigit():
                        print(f"   -> [FAIL] Found Numeric Heading: '{block.get('text')}'")

            
            print(f"\nSummary: {counts}")
            
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_extraction()
