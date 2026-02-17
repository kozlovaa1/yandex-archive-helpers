import time
import os
import json
import notion_helper
from urllib.parse import urlparse

DATA_FILE = "received_data.json"

def process_data(data):
    print(f"Processing {len(data)} items...")
    cases_cache = notion_helper.get_existing_cases()
    processed_count = 0
    
    for item in data:
        title = item.get("title")
        raw_href = item.get("url")
        meta_text = item.get("meta")
        text_content = item.get("text", "")
        
        if not title: continue
        
        # Filter
        if "Яшкино" in title or "Еманжелинской" in title:
            print(f"Filtered: {title}")
            continue
            
        # Clean URL
        if raw_href:
            path = urlparse(raw_href).path
            full_url = f"https://yandex.ru{path}"
        else:
            full_url = ""
            
        # Parse Meta
        if meta_text and "стр." in meta_text:
            parts = meta_text.split("стр.")
            case_code = parts[0].strip().rstrip(",")
            page_number = parts[-1].strip()
        else:
            case_code = meta_text or "Unknown Case"
            page_number = "1"
            
        print(f"Processing: {title} | {case_code}")
        
        # Notion
        case_id = cases_cache.get(case_code)
        if not case_id:
            print(f"  -> Creating Case: {case_code}")
            case_id = notion_helper.create_page(notion_helper.ROOT_PAGE_ID, case_code)
            if case_id:
                cases_cache[case_code] = case_id
            else:
                continue
        
        page_title = f"Стр. {page_number}"
        existing = notion_helper.get_existing_pages(case_id)
        
        if page_title in existing:
            # Check content? No, just skip for now to be fast
            # Or assume user wants to update (add text)
            print("  -> Page exists. Skipping.")
            continue
            
        if not text_content:
            text_content = "Текст не был получен (ошибка JS?)."
            
        res = notion_helper.create_page(case_id, page_title, text_content, full_url)
        if res:
            processed_count += 1
            print(f"  -> Saved")

    print(f"Batch finished. Saved {processed_count} items.")

def main():
    print(f"Watching {DATA_FILE}...")
    last_mtime = 0
    
    while True:
        if os.path.exists(DATA_FILE):
            mtime = os.path.getmtime(DATA_FILE)
            if mtime > last_mtime:
                # Wait a bit for write to finish
                time.sleep(0.5)
                try:
                    with open(DATA_FILE, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if not content: continue
                        data = json.loads(content)
                    
                    print("\n--- New Data Received ---")
                    process_data(data)
                    
                    # Clear file to avoid re-processing?
                    # Or rename it to history
                    os.rename(DATA_FILE, f"data_processed_{time.time()}.json")
                    
                except Exception as e:
                    print(f"Error processing: {e}")
                
                last_mtime = time.time() # Update to now (since file is gone or updated)
        
        time.sleep(1)

if __name__ == "__main__":
    main()
