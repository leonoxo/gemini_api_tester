# -*- coding: utf-8 -*-
# 程式碼功能：整理並去除重複的 API Key

def 整理並去重API_Key(原始文本: str) -> list[str]:
    """
    整理 API Key 列表，去除重複的 Key，並進行排序。

    Args:
        原始文本 (str): 包含 API Key 的原始字串，可能包含引號和多行。

    Returns:
        list[str]: 整理並去重後的 API Key 列表，已排序。
    """
    # 1. 初步清理：移除文本首尾可能的空白字符
    清理後文本 = 原始文本.strip()

    # 2. 移除可能的外部引號（如 「 和 」）
    #    假設這些引號僅用於包圍整個文本塊，而不是 Key 的一部分
    if 清理後文本.startswith("「"):
        清理後文本 = 清理後文本[1:]
    if 清理後文本.endswith("」"):
        清理後文本 = 清理後文本[:-1]
    
    # 再次清理，以移除引號與實際內容間可能存在的空格
    清理後文本 = 清理後文本.strip()

    # 3. 按行分割 API Key
    所有可能的Key列表 = 清理後文本.splitlines()

    # 4. 清理每個 Key 並過濾空字串
    #    - key.strip(): 移除每個 Key 字串前後的空白
    #    - if key.strip(): 確保不是空字串或僅包含空白的字串
    已處理的Key列表 = [key.strip() for key in 所有可能的Key列表 if key.strip()]

    # 5. 去除重複的 Key 並排序
    #    - 使用 set 資料結構自動去重
    #    - 再轉換回 list 並使用 sorted() 排序，使輸出結果具有一致性
    不重複的Key列表 = sorted(list(set(已處理的Key列表)))

    return 不重複的Key列表

# 主程式邏輯
if __name__ == "__main__":
    api_key_file_path = "/data/check_keys.txt"
    輸入的API_Key內容 = "" # 初始化變數
    try:
        with open(api_key_file_path, 'r', encoding='utf-8') as f:
            輸入的API_Key內容 = f.read()
    except FileNotFoundError:
        print(f"錯誤：找不到 API Key 檔案 '{api_key_file_path}'。請確認檔案是否存在。")
    except Exception as e:
        print(f"讀取 API Key 檔案時發生錯誤：{e}")

    整理後的列表 = 整理並去重API_Key(輸入的API_Key內容)

    print("\n已整理並去除重複的 API Key 如下 (一行一個，並已排序)：")
    print("=======================================================")
    if 整理後的列表:
        for key in 整理後的列表:
            print(key)
        print("=======================================================")
        print(f"總共找到 {len(整理後的列表)} 個不重複的 API Key。")
    else:
        print("未找到任何有效的 API Key。")
        print("=======================================================")

    # 關於 API Key 安全性的提醒
    print("\n重要提醒：")
    print("  * API Key 通常是敏感資訊，請務必妥善保管，避免在公開的程式碼庫、論壇或不安全的環境中洩漏。")
    print("  * 若這些 Key 並非由您本人產生或從可信任的管道獲得，建議您謹慎使用，並充分了解其可能的安全風險。")
    print("  * 定期檢查並更換 API Key 也是一個良好的安全習慣。")
