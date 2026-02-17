import requests
import os
import json
import sys

# Setup
NOTION_KEY = "ВАШ КЛЮЧ API NOTION"
ROOT_PAGE_ID = "ID страницы Notion для сохранения результата"
HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_existing_cases():
    """Returns a dict of {case_title: page_id} for existing cases under root."""
    url = f"https://api.notion.com/v1/blocks/{ROOT_PAGE_ID}/children"
    cases = {}
    has_more = True
    next_cursor = None
    
    print("Fetching existing cases...")
    while has_more:
        params = {}
        if next_cursor: params["start_cursor"] = next_cursor
        
        try:
            r = requests.get(url, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            
            for block in data.get("results", []):
                if block["type"] == "child_page":
                    title = block["child_page"]["title"]
                    cases[title] = block["id"]
            
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        except Exception as e:
            print(f"Error fetching cases: {e}")
            break
            
    print(f"Found {len(cases)} existing cases.")
    return cases

def get_existing_pages(case_id):
    """Returns a list of page titles under a case page."""
    url = f"https://api.notion.com/v1/blocks/{case_id}/children"
    pages = []
    has_more = True
    next_cursor = None
    
    while has_more:
        params = {}
        if next_cursor: params["start_cursor"] = next_cursor
        
        try:
            r = requests.get(url, headers=HEADERS, params=params)
            r.raise_for_status()
            data = r.json()
            
            for block in data.get("results", []):
                if block["type"] == "child_page":
                    title = block["child_page"]["title"]
                    pages.append(title)
            
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
        except Exception as e:
            print(f"Error fetching pages for case {case_id}: {e}")
            break
            
    return pages

def create_page(parent_id, title, text_content=None, link=None):
    """Creates a new child page."""
    url = "https://api.notion.com/v1/pages"
    
    children = []
    if link:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": f"Ссылка на источник: {link}",
                        "link": {"url": link}
                    }
                }]
            }
        })
    
    if text_content:
        # Split text into 2000 char chunks to avoid Notion limits
        chunks = [text_content[i:i+2000] for i in range(0, len(text_content), 2000)]
        for chunk in chunks:
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": chunk}}]
                }
            })

    payload = {
        "parent": {"page_id": parent_id},
        "properties": {
            "title": {"title": [{"text": {"content": title}}]}
        },
        "children": children
    }
    
    try:
        r = requests.post(url, headers=HEADERS, json=payload)
        if r.status_code != 200:
            print(f"Error creating page '{title}': {r.status_code} {r.text}")
            return None
        return r.json()["id"]
    except Exception as e:
        print(f"Exception creating page: {e}")
        return None

if __name__ == "__main__":
    action = sys.argv[1]
    
    if action == "cache":
        cases = get_existing_cases()
        with open("notion_cache.json", "w") as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
            
    elif action == "check_page":
        case_id = sys.argv[2]
        page_title = sys.argv[3]
        existing = get_existing_pages(case_id)
        if page_title in existing:
            print("EXISTS")
        else:
            print("NEW")
            
    elif action == "create_case":
        title = sys.argv[2]
        page_id = create_page(ROOT_PAGE_ID, title)
        if page_id:
            print(page_id)
        else:
            print("ERROR")

    elif action == "create_subpage":
        parent_id = sys.argv[2]
        title = sys.argv[3]
        link = sys.argv[4]
        # Text is passed via stdin
        text = sys.stdin.read()
        page_id = create_page(parent_id, title, text, link)
        if page_id:
            print(page_id)
        else:
            print("ERROR")
