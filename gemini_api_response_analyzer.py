import google.generativeai as genai
import google.generativeai.client as client
import google.generativeai.models as models
import random
import time
import datetime
import logging
from typing import List, Tuple, Optional
from pathlib import Path
from google.api_core.exceptions import GoogleAPIError, ClientError

# 設定日誌配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

API_ANALYZER_CONFIG = {
    "API_KEYS_FILE": "api_keys.txt",
    "MIN_TEST_INTERVAL_SECONDS": 2,
    "MAX_TEST_INTERVAL_SECONDS": 5,
    "DEFAULT_CHAT_MODEL": "gemma-3-1b-it"
}


class GeminiAPIResponseAnalyzer:
    """
    Gemini API 回應分析工具。
    負責測試 API 金鑰並根據回應狀態 (200, 429) 進行分類和儲存。
    """

    def __init__(self, api_keys_path: Path):
        """
        初始化 GeminiAPIResponseAnalyzer 實例。

        Args:
            api_keys_path (Path): API 密鑰檔案的路徑。
        """
        self.api_keys_path = api_keys_path
        self.script_dir = api_keys_path.parent
        self.keys_200: List[str] = []
        self.keys_429: List[str] = []
        self.invalid_keys: List[str] = []
        self.model_list: List = []
        self.model_fetch_key: Optional[str] = None
        self.model_fetch_error: Optional[str] = None

    def _configure_gemini_client(self, api_key: str) -> None:
        """
        配置 Gemini API 客戶端。

        Args:
            api_key (str): 要配置的 API 密鑰。
        """
        client.configure(api_key=api_key)

    def load_api_keys(self) -> List[str]:
        """
        從文件中讀取 API 密鑰。

        Returns:
            List[str]: API 密鑰列表。
        """
        try:
            if not self.api_keys_path.exists():
                logger.error(f"API 密鑰檔案 '{self.api_keys_path}' 不存在。請確保檔案存在並包含有效的 API 密鑰。")
                return []
            with open(self.api_keys_path, 'r', encoding='utf-8') as f:
                keys = [line.strip() for line in f if line.strip()]
            logger.info(f"從檔案 '{self.api_keys_path}' 中讀取了 {len(keys)} 個 API 密鑰。")
            return keys
        except Exception as e:
            logger.error(f"讀取 API 密鑰檔案 '{self.api_keys_path}' 時發生錯誤: {e}")
            return []

    def fetch_model_list(self, api_keys: List[str]) -> None:
        """
        嘗試使用 API 密鑰列表中的第一個有效密鑰來獲取模型列表。
        """
        logger.info("正在嘗試使用一個有效的 API 密鑰獲取模型列表...")
        for key in api_keys:
            try:
                self._configure_gemini_client(key)
                self.model_list = models.list_models()
                self.model_fetch_key = key
                logger.info(f"成功使用 API 密鑰 ({key[:8]}...) 獲取模型列表。")
                return
            except Exception as e:
                logger.warning(f"使用 API 密鑰 ({key[:8]}...) 獲取模型列表失敗: {e}")
                continue
        self.model_fetch_error = "未能使用任何提供的 API 密鑰成功獲取模型列表。"
        logger.error(self.model_fetch_error)

    def perform_text_chat_test(self, api_key: str, model_name: str = API_ANALYZER_CONFIG["DEFAULT_CHAT_MODEL"]) -> Tuple[bool, str]:
        """
        使用指定的 API 密鑰和模型進行簡單的文字對話測試。

        Returns:
            Tuple[bool, str]: (是否成功, 回應文字或錯誤訊息)。
        """
        try:
            self._configure_gemini_client(api_key)
            model = genai.GenerativeModel(model_name)
            chat = model.start_chat(history=[])
            message = "請給我一個簡單的建議。"
            logger.info(f"API 密鑰 ({api_key[:8]}...) 正在發送訊息到模型 '{model_name}'。")
            response = chat.send_message(message, generation_config={"max_output_tokens": 10})
            if response.text:
                logger.info(f"API 密鑰 ({api_key[:8]}...) 對話測試成功。")
                return True, response.text
            else:
                logger.warning(f"API 密鑰 ({api_key[:8]}...) 對話測試成功，但回覆為空。")
                return True, "回覆為空"
        except GoogleAPIError as e:
            error_message = str(e)
            if "429" in error_message or "Quota exceeded" in error_message:
                logger.warning(f"API 密鑰 ({api_key[:8]}...) 遇到 429 錯誤 (Quota exceeded)。錯誤訊息: {error_message}")
                return True, error_message  # 仍視為成功，但在調用處處理分類
            logger.warning(f"API 密鑰 ({api_key[:8]}...) 對話測試失敗，Google API 錯誤: {error_message}")
            return False, error_message
        except ClientError as e:
            logger.warning(f"API 密鑰 ({api_key[:8]}...) 對話測試失敗，客戶端錯誤: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"API 密鑰 ({api_key[:8]}...) 對話測試時發生意外錯誤: {e}")
            return False, f"意外錯誤: {e}"

    def save_categorized_keys(self) -> None:
        """
        將分類後的 API 密鑰儲存到對應的檔案中。
        檔案名稱格式為 YYYYMMDD_200.txt 和 YYYYMMDD_429.txt。
        """
        current_date_str = datetime.datetime.now().strftime("%Y%m%d")
        path_200 = Path(".") / f"{current_date_str}_200.txt"
        path_429 = Path(".") / f"{current_date_str}_429.txt"

        try:
            if self.keys_200:
                with open(path_200, 'w', encoding='utf-8') as f:
                    for key in self.keys_200:
                        f.write(key + "\n")
                logger.info(f"所有 {len(self.keys_200)} 個 200 回應的 API 密鑰已成功儲存至檔案：'{path_200}'")
            else:
                logger.info("沒有找到 200 回應的 API 密鑰，未產生 _200.txt 檔案。")

            if self.keys_429:
                with open(path_429, 'w', encoding='utf-8') as f:
                    for key in self.keys_429:
                        f.write(key + "\n")
                logger.info(f"所有 {len(self.keys_429)} 個 429 回應的 API 密鑰已成功儲存至檔案：'{path_429}'")
            else:
                logger.info("沒有找到 429 回應的 API 密鑰，未產生 _429.txt 檔案。")

        except Exception as e:
            logger.error(f"儲存分類的 API 密鑰時發生錯誤: {e}")

    def _perform_single_key_test(self, key: str, key_index: int, total_keys: int) -> None:
        """
        對單個 API 密鑰執行測試並進行分類。
        """
        logger.info(f"正在測試 API 密鑰 {key_index+1}/{total_keys}: {key[:8]}...")
        
        target_model = API_ANALYZER_CONFIG["DEFAULT_CHAT_MODEL"]
        chat_success, chat_result = self.perform_text_chat_test(key, target_model)

        if chat_success:
            if "429" in chat_result or "Quota exceeded" in chat_result:
                self.keys_429.append(key)
                logger.info(f"API 密鑰 ({key[:8]}...) 分類為 429 (Quota Exceeded)。")
            else:
                self.keys_200.append(key)
                logger.info(f"API 密鑰 ({key[:8]}...) 分類為 200 (成功)。")
        else:
            self.invalid_keys.append(key)
            logger.warning(f"API 密鑰 ({key[:8]}...) 測試失敗：{chat_result}，分類為無效。")

    def run_tests(self) -> None:
        """
        執行 API 金鑰測試和分類的主邏輯。
        """
        logger.info("開始 Gemini API 回應分析測試...")
        api_keys = self.load_api_keys()
        if not api_keys:
            logger.error("沒有找到 API 密鑰，測試終止。")
            return

        logger.info(f"將測試 {len(api_keys)} 個 API 密鑰。")
        
        # 雖然此腳本主要關注聊天測試，但保留獲取模型列表的邏輯有助於初步篩選
        self.fetch_model_list(api_keys)

        for i, key in enumerate(api_keys):
            self._perform_single_key_test(key, i, len(api_keys))

            if i < len(api_keys) - 1:
                sleep_duration = random.randint(API_ANALYZER_CONFIG["MIN_TEST_INTERVAL_SECONDS"], API_ANALYZER_CONFIG["MAX_TEST_INTERVAL_SECONDS"])
                logger.info(f"等待 {sleep_duration} 秒後進行下一次測試...")
                time.sleep(sleep_duration)

        self.save_categorized_keys()
        self._log_summary()

    def _log_summary(self) -> None:
        """
        記錄測試結果的總結資訊。
        """
        total_tested = len(self.keys_200) + len(self.keys_429) + len(self.invalid_keys)
        logger.info("--- 測試總結 ---")
        logger.info(f"總共測試的 API 密鑰數量：{total_tested}")
        logger.info(f"200 (成功) 的 API 密鑰數量：{len(self.keys_200)}")
        logger.info(f"429 (請求過多) 的 API 密鑰數量：{len(self.keys_429)}")
        logger.info(f"無效的 API 密鑰數量：{len(self.invalid_keys)}")
        logger.info("測試完成。")


def main() -> None:
    """主函數，啟動 Gemini API 回應分析。"""
    api_keys_path = Path(API_ANALYZER_CONFIG["API_KEYS_FILE"])
    analyzer = GeminiAPIResponseAnalyzer(api_keys_path)
    analyzer.run_tests()


if __name__ == "__main__":
    main()