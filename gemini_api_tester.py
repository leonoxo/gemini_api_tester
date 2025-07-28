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

API_TESTER_CONFIG = {
    "API_KEYS_FILE": "api_keys.txt",
    "MIN_TEST_INTERVAL_SECONDS": 2,
    "MAX_TEST_INTERVAL_SECONDS": 5,
    "DEFAULT_CHAT_MODEL": "gemma-3-1b-it"
}


class GeminiAPITester:
    """
    Gemini API 密鑰測試工具類別。
    負責管理 API 密鑰的讀取、測試和結果儲存。
    """

    def __init__(self, api_keys_path: Path):
        """
        初始化 GeminiAPITester 實例。

        Args:
            api_keys_path (Path): API 密鑰檔案的路徑。
        """
        self.api_keys_path = api_keys_path
        self.script_dir = api_keys_path.parent
        self.valid_keys: List[str] = []
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
        結果儲存在實例變數 `self.model_list` 和 `self.model_fetch_key` 中。
        如果失敗，錯誤訊息儲存在 `self.model_fetch_error` 中。

        Args:
            api_keys (List[str]): API 密鑰列表。
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

    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[str]]:
        """
        測試單個 API 密鑰的基本配置有效性，透過嘗試列出模型。

        Args:
            api_key (str): 要測試的 API 密鑰。

        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 錯誤訊息)。
        """
        try:
            self._configure_gemini_client(api_key)
            models.list_models()
            return True, None
        except GoogleAPIError as e:
            return False, f"Google API 錯誤: {e}"
        except Exception as e:
            logger.error(f"測試 API 密鑰 ({api_key[:8]}...) 時發生意外錯誤: {e}")
            return False, f"意外錯誤: {e}"

    def perform_text_chat_test(self, api_key: str, model_name: str = API_TESTER_CONFIG["DEFAULT_CHAT_MODEL"]) -> Tuple[bool, str]:
        """
        使用指定的 API 密鑰和模型進行簡單的文字對話測試，使用大約10個token。

        Args:
            api_key (str): 要使用的 API 密鑰。
            model_name (str): 要使用的模型名稱，預設為配置文件中的值。

        Returns:
            Tuple[bool, str]: (是否成功, 回應文字或錯誤訊息)。
        """
        try:
            self._configure_gemini_client(api_key)
            model = genai.GenerativeModel(model_name)
            chat = model.start_chat(history=[])
            messages = [
                "請描述今天的天气。",
                "你能告訴我一個簡單的事實嗎？",
                "分享一個有趣的小知識。",
                "你對科技有什麼看法？",
                "請給我一個簡單的建議。"
            ]
            message = random.choice(messages)
            logger.info(f"API 密鑰 ({api_key[:8]}...) 正在發送訊息：'{message}' 到模型 '{model_name}'。")
            response = chat.send_message(message, generation_config={"max_output_tokens": 10})
            if response.text:
                logger.info(f"API 密鑰 ({api_key[:8]}...) 對話測試成功，回覆：'{response.text[:50]}...'")
                return True, response.text
            else:
                logger.warning(f"API 密鑰 ({api_key[:8]}...) 對話測試成功，但回覆為空。")
                return True, "回覆為空"
        except GoogleAPIError as e:
            error_message = str(e)
            if "429" in error_message or "Quota exceeded" in error_message:
                logger.warning(f"API 密鑰 ({api_key[:8]}...) 遇到 429 錯誤 (Quota exceeded)，仍視為有效。錯誤訊息: {error_message}")
                return True, error_message
            logger.warning(f"API 密鑰 ({api_key[:8]}...) 對話測試失敗，Google API 錯誤: {error_message}")
            return False, error_message
        except ClientError as e:
            logger.warning(f"API 密鑰 ({api_key[:8]}...) 對話測試失敗，客戶端錯誤: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"API 密鑰 ({api_key[:8]}...) 對話測試時發生意外錯誤: {e}")
            return False, f"意外錯誤: {e}"

    def save_verified_keys(self) -> None:
        """
        將有效的 API 密鑰儲存到檔案中。
        檔案名稱格式為 api_keys_verified_YYYYMMDD.txt。
        """
        if not self.valid_keys:
            logger.info("沒有找到有效的 API 密鑰，因此未產生已驗證的密鑰檔案。")
            return

        current_date_str = datetime.datetime.now().strftime("%Y%m%d")
        verified_keys_filename = f"api_keys_verified_{current_date_str}.txt"
        verified_keys_filepath = Path("/data") / verified_keys_filename

        try:
            with open(verified_keys_filepath, 'w', encoding='utf-8') as vf:
                for verified_key in self.valid_keys:
                    vf.write(verified_key + "\n")
            logger.info(f"所有 {len(self.valid_keys)} 個有效的 API 密鑰已成功儲存至檔案：'{verified_keys_filepath}'")
        except Exception as e:
            logger.error(f"無法將有效的 API 密鑰寫入檔案 '{verified_keys_filepath}': {e}")
            logger.info("以下是已找到的有效密鑰，請手動複製：")
            for verified_key in self.valid_keys:
                logger.info(verified_key)

    def _perform_single_key_tests(self, key: str, key_index: int, total_keys: int) -> None:
        """
        對單個 API 密鑰執行基本配置和文字對話測試。

        Args:
            key (str): 要測試的 API 密鑰。
            key_index (int): 密鑰在列表中的索引 (用於日誌)。
            total_keys (int): 總密鑰數量 (用於日誌)。
        """
        logger.info(f"正在測試 API 密鑰 {key_index+1}/{total_keys}: {key[:8]}...")

        # 步驟 1: 基本配置有效性測試
        is_valid_config, config_error_message = self.validate_api_key(key)
        if not is_valid_config:
            self.invalid_keys.append(key)
            logger.warning(f"API 密鑰 ({key[:8]}...) 基本配置無效。錯誤訊息: {config_error_message}")
            return

        logger.info(f"API 密鑰 ({key[:8]}...) 通過基本配置有效性測試。")

        # 步驟 2: 文字對話測試
        target_model = API_TESTER_CONFIG["DEFAULT_CHAT_MODEL"]
        logger.info(f"API 密鑰 ({key[:8]}...) 正在使用模型 '{target_model}' 進行文字對話測試...")
        chat_success, chat_result = self.perform_text_chat_test(key, target_model)

        if chat_success:
            self.valid_keys.append(key)
            logger.info(f"API 密鑰 ({key[:8]}...) 對話測試成功，密鑰分類為有效。")
        else:
            self.invalid_keys.append(key)
            logger.warning(f"API 密鑰 ({key[:8]}...) 對話測試失敗：{chat_result}，密鑰分類為無效。")

    def run_tests(self) -> None:
        """
        執行 Gemini API 密鑰有效性測試的主邏輯。
        依序載入密鑰、獲取模型列表，然後對每個密鑰執行測試。
        """
        logger.info("開始 Gemini API 密鑰有效性測試...")
        api_keys = self.load_api_keys()
        if not api_keys:
            logger.error("沒有找到 API 密鑰，測試終止。")
            return

        logger.info(f"將測試 {len(api_keys)} 個 API 密鑰。")
        self.fetch_model_list(api_keys)

        if self.model_fetch_key:
            logger.info(f"模型列表已使用 API 密鑰 '{self.model_fetch_key[:8]}...' 獲取。後續有效密鑰將使用此列表。")
        elif self.model_fetch_error:
            logger.error(f"獲取模型列表時發生錯誤: {self.model_fetch_error}")

        for i, key in enumerate(api_keys):
            self._perform_single_key_tests(key, i, len(api_keys))

            if i < len(api_keys) - 1:
                sleep_duration = random.randint(API_TESTER_CONFIG["MIN_TEST_INTERVAL_SECONDS"], API_TESTER_CONFIG["MAX_TEST_INTERVAL_SECONDS"])
                logger.info(f"等待 {sleep_duration} 秒後進行下一次測試...")
                time.sleep(sleep_duration)

        self.save_verified_keys()
        self._log_summary()

    def _log_summary(self) -> None:
        """
        記錄測試結果的總結資訊。
        """
        logger.info("測試總結")
        logger.info(f"總共測試的 API 密鑰數量：{len(self.valid_keys) + len(self.invalid_keys)}")
        logger.info(f"有效的 API 密鑰數量：{len(self.valid_keys)}")
        logger.info(f"無效的 API 密鑰數量：{len(self.invalid_keys)}")

        if self.model_fetch_key:
            logger.info(f"模型列表是使用 API 密鑰 '{self.model_fetch_key[:8]}...' 獲取的。")
        elif self.model_fetch_error:
            logger.error(f"嘗試獲取模型列表時出錯: {self.model_fetch_error}")
        else:
            logger.error("未能使用任何密鑰獲取模型列表（可能所有密鑰都無效，或在獲取模型列表前就已失敗）。")
        logger.info("測試完成。")



def main() -> None:
    """主函數，啟動 Gemini API 密鑰有效性測試。"""
    # 將金鑰檔案的路徑指向 /data 目錄，以便於 Docker 掛載
    api_keys_path = Path("/data") / API_TESTER_CONFIG["API_KEYS_FILE"]
    tester = GeminiAPITester(api_keys_path)
    tester.run_tests()


if __name__ == "__main__":
    main()