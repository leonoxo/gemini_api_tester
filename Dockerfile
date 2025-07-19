# 步驟 1: 使用官方 Python 映像檔作為基礎
# 我們選擇 'slim' 版本以獲得更小的映像檔體積
FROM python:3.11-slim

# 步驟 2: 在容器內設定工作目錄
WORKDIR /app

# 步驟 3: 複製依賴性定義檔
# 這樣做可以利用 Docker 的層快取。只要 requirements.txt 沒有變更，就不會重新安裝套件。
COPY requirements.txt .

# 步驟 4: 安裝 Python 依賴套件
# --no-cache-dir 選項可以減少映像檔大小
RUN pip install --no-cache-dir -r requirements.txt

# 步驟 5: 將您的應用程式程式碼複製到容器中
COPY *.py ./

# 步驟 6: 設定容器啟動時的預設指令
# 由於有兩個主要腳本，我們不設定固定的 ENTRYPOINT。
# 使用者可以在 `docker run` 指令中輕鬆指定要執行的腳本，提供更大的靈活性。
# 例如: docker run <image_name> python check_for_duplicate_keys.py
# 或:   docker run <image_name> python gemini_api_tester.py
CMD ["python"]