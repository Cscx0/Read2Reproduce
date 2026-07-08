import json
import unittest
from unittest.mock import patch

import httpx

from app.config import get_settings
from app.services import llm_client


class LLMClientTest(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()

    def test_chat_completion_url_accepts_base_url_or_full_endpoint(self) -> None:
        self.assertEqual(
            llm_client._chat_completion_url("https://api.example.com/v1"),
            "https://api.example.com/v1/chat/completions",
        )
        self.assertEqual(
            llm_client._chat_completion_url("https://api.example.com/chat/completions"),
            "https://api.example.com/chat/completions",
        )

    def test_parse_json_object_accepts_fenced_and_prefixed_json(self) -> None:
        self.assertEqual(llm_client._parse_json_object('```json\n{"ok": true}\n```'), {"ok": True})
        self.assertEqual(llm_client._parse_json_object('好的：\n{"ok": true, "items": [1, 2]}\n完成'), {"ok": True, "items": [1, 2]})

    @patch("app.services.llm_client.httpx.post")
    def test_call_retries_without_response_format(self, post) -> None:
        bad_request = httpx.Response(
            400,
            json={"error": {"message": "response_format is unsupported"}},
            request=httpx.Request("POST", "https://api.example.com/chat/completions"),
        )
        success = httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"ok": True, "message": "pong"}),
                        }
                    }
                ]
            },
            request=httpx.Request("POST", "https://api.example.com/chat/completions"),
        )
        post.side_effect = [bad_request, success]

        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_BASE_URL": "https://api.example.com",
                "LLM_MODEL": "test-model",
                "LLM_RESPONSE_FORMAT_JSON": "true",
            },
            clear=False,
        ):
            get_settings.cache_clear()
            result = llm_client._call_chat_completion("{}", "llm_probe")

        self.assertEqual(result, {"ok": True, "message": "pong"})
        self.assertEqual(post.call_count, 2)
        first_payload = post.call_args_list[0].kwargs["json"]
        second_payload = post.call_args_list[1].kwargs["json"]
        self.assertIn("response_format", first_payload)
        self.assertNotIn("response_format", second_payload)


if __name__ == "__main__":
    unittest.main()
