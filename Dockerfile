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

# 步驟 5: 建立一個用於存放資料的目錄
RUN mkdir /data

# 步驟 6: 將您的應用程式程式碼複製到容器中
COPY *.py ./

# 步驟 7: 設定容器啟動時的預設指令
# 預設執行主測試腳本
CMD ["python", "gemini_api_tester.py"]