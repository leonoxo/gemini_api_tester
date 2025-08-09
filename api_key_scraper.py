import requests
import re
import sys
import json

def load_config():
    """Loads configuration from config.json."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("錯誤：找不到 config.json 檔案。", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print("錯誤：config.json 檔案格式不正確。", file=sys.stderr)
        return None

def scrape_api_keys(cookies):
    """
    Scrapes API keys from the website using the provided cookies.
    """
    print("--- 開始爬取所有分頁的 API Keys ---")
    base_url = "https://geminikeyseeker.o0o.moe/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    all_api_keys = set() # Use a set to avoid duplicates
    page = 1
    consecutive_empty_pages = 0
    max_consecutive_empty = 3 # Stop after 3 consecutive empty pages

    try:
        while True:
            if consecutive_empty_pages >= max_consecutive_empty:
                print(f"\n已連續 {max_consecutive_empty} 頁找不到 API key，判斷已達末頁。")
                break

            params = {'status': '200', 'page': page}
            print(f"\n--- 正在爬取第 {page} 頁 ---")
            print(f"1. 正在向 {base_url} 發送 GET 請求 (參數: {params})...")
            response = requests.get(base_url, params=params, cookies=cookies, headers=headers, timeout=20)
            print(f"2. 收到回應，狀態碼: {response.status_code}")

            if response.status_code != 200:
                print(f"錯誤：第 {page} 頁請求失敗，狀態碼: {response.status_code}。跳過此頁。")
                consecutive_empty_pages += 1
                page += 1
                continue

            if page == 1 and "leonoxo" not in response.text:
                print("錯誤：登入可能失敗。在第一頁內容中找不到使用者名稱。")
                print("爬取中止。")
                return

            print(f"3. 正在搜尋第 {page} 頁的 API keys...")
            api_keys_on_page = re.findall(r'AIzaSy[A-Za-z0-9_-]{33}', response.text)
            
            if api_keys_on_page:
                found_count = len(all_api_keys)
                all_api_keys.update(api_keys_on_page)
                new_keys_count = len(all_api_keys) - found_count
                print(f"4. 在第 {page} 頁找到 {len(api_keys_on_page)} 個 API keys ({new_keys_count} 個不重複)。")
                consecutive_empty_pages = 0 # Reset counter if keys are found
            else:
                print(f"4. 在第 {page} 頁找不到任何 API keys。")
                consecutive_empty_pages += 1
            
            page += 1

    except requests.exceptions.Timeout:
        print("錯誤：請求超時。", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"錯誤：請求失敗 - {e}", file=sys.stderr)
    except Exception as e:
        print(f"發生未預期的錯誤: {e}", file=sys.stderr)
    finally:
        print("\n--- 所有頁面爬取結束 ---")
        if all_api_keys:
            print(f"總共找到 {len(all_api_keys)} 個不重複的 API keys。")
            with open("found_api_keys.txt", "w") as f:
                for key in sorted(list(all_api_keys)): # Sort for consistent output
                    f.write(key + "\n")
            print("所有 API keys 已儲存至 found_api_keys.txt")
        else:
            print("在所有頁面中都沒有找到任何 API keys。")

if __name__ == "__main__":
    config = load_config()
    if config and "cookies" in config:
        scrape_api_keys(config["cookies"])