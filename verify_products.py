
import json
import sys

def verify_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        total = len(data)
        missing_link = 0
        missing_image = 0
        missing_html = 0
        
        for item in data:
            if not item.get('link'):
                missing_link += 1
            if not item.get('image'):
                missing_image += 1
            if not item.get('html_text'):
                missing_html += 1
                
        print(f"Total Products: {total}")
        print(f"Missing Link: {missing_link}")
        print(f"Missing Image: {missing_image}")
        print(f"Missing HTML text: {missing_html}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        verify_json(sys.argv[1])
    else:
        print("Please provide a file path.")
