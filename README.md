# Gemini API Tester

這是一個用於批量驗證 Google Gemini API 金鑰有效性的 Python 工具。它可以幫助您快速從大量金鑰中篩選出可用的金鑰。

## ✨ 功能

- **批量測試**：自動化測試列表中的所有 API 金鑰。
- **金鑰清理**：提供輔助腳本，用於移除重複的金鑰並整理格式。
- **詳細日誌**：在測試過程中提供清晰的日誌輸出，方便追蹤狀態。
- **結果保存**：自動將通過驗證的有效金鑰保存到新的檔案中。
- **安全設計**：預設使用 `.gitignore` 忽略所有 `.txt` 檔案，避免 API 金鑰意外洩漏至版本控制中。

## 🚀 開始使用

有兩種主要的使用方式：**透過 Docker（推薦）** 或 **直接使用 Python**。

### 🐳 透過 Docker 執行 (推薦)

使用 Docker 可以免去管理 Python 環境和依賴性的麻煩，確保程式在任何地方都能以相同的方式運行。

**先決條件**:
- [Docker](https://www.docker.com/get-started) 已安裝在您的系統上。

**執行步驟**:

1.  **克隆儲存庫**:
    ```bash
    git clone https://github.com/leonoxo/Gemini_API_Tester.git
    cd Gemini_API_Tester
    ```

2.  **建立 Docker 映像檔**:
    在專案根目錄下，執行以下指令來建立一個名為 `leonoxo/gemini_api_tester` 的 Docker 映像檔。
    ```bash
    docker build -t leonoxo/gemini_api_tester .
    ```

3.  **執行容器化腳本**:
    - **清理金鑰**:
      - 將 `check_keys.txt.example` 複製為 `check_keys.txt`。
      - 將您的原始金鑰放入 `check_keys.txt`。
      - 執行以下指令。`-v` 參數會將您當前的目錄掛載到容器的 `/app` 目錄，讓容器可以讀寫您的 `.txt` 檔案。
      ```bash
      docker run --rm -v "$(pwd):/app" leonoxo/gemini_api_tester python check_for_duplicate_keys.py
      ```
      - 將終端輸出的乾淨金鑰列表貼到 `api_keys.txt` (如果需要，請先從 `api_keys.txt.example` 複製)。
    
    - **驗證金鑰**:
      - 確保 `api_keys.txt` 已包含清理後的金鑰。
      - 執行以下指令：
      ```bash
      docker run --rm -v "$(pwd):/app" leonoxo/gemini_api_tester python gemini_api_tester.py
      ```
      測試完成後，包含有效金鑰的 `api_keys_verified_YYYYMMDD.txt` 檔案會出現在您的專案目錄中。

---

### 🐍 直接使用 Python 執行

**先決條件**:
- Python 3.x

**安裝**:

1.  **克隆儲存庫**:
    ```bash
    git clone https://github.com/leonoxo/gemini_api_tester.git
    cd gemini_api_tester
    ```

2.  **安裝依賴**:
    ```bash
    pip install -r requirements.txt
    ```

**使用流程**:

1.  **步驟一：準備金鑰**
    - 將 `check_keys.txt.example` 複製為 `check_keys.txt`。
    - 將您收集到的所有原始 API 金鑰（可能包含重複或格式混亂）貼到 `check_keys.txt` 檔案中。

2.  **步驟二：清理與去重**
    執行 `check_for_duplicate_keys.py` 腳本來清理金鑰：
    ```bash
    python check_for_duplicate_keys.py
    ```
    此腳本會將整理好的、不重複的金鑰列表輸出到終端機。

3.  **步驟三：準備測試**
    - 將 `api_keys.txt.example` 複製為 `api_keys.txt`。
    - 將終端機中輸出的乾淨金鑰列表複製並完全覆蓋到 `api_keys.txt` 檔案中。

4.  **步驟四：執行驗證**
    執行主測試腳本 `gemini_api_tester.py`：
    ```bash
    python gemini_api_tester.py
    ```
    腳本會開始測試，並顯示詳細進度。

5.  **步驟五：獲取結果**
    測試完成後，所有有效的金鑰將被保存在一個新檔案中，檔名格式為 `api_keys_verified_YYYYMMDD.txt`。

## ⚠️ 安全提醒

**重要提醒**：此專案包含的 `.gitignore` 檔案會忽略所有 `.txt` 檔案。這是為了防止您將包含敏感 API 金鑰的檔案意外上傳到 GitHub。

請**不要**修改 `.gitignore` 檔案來追蹤 `.txt` 檔案，並確保您的私有金鑰始終保持在本地，不要提交到任何公開的儲存庫中。