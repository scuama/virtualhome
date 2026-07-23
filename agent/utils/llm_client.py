import os
import json
import openai
import base64
from typing import Optional
from urllib import request, error
import ssl
import time
import re

# Bypass dead local proxies
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']:
    os.environ.pop(k, None)


def _resolve_api_key(explicit_key: Optional[str] = None) -> str:
    if explicit_key:
        return explicit_key.strip()
    return os.environ.get("OPENAI_API_KEY", "")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

class LLMClient:
    def __init__(self, model_name="gpt-5.4-mini", api_key: Optional[str] = None, base_url=None):
        """
        初始化 LLM 客户端。默认使用 gpt-5.4-mini。
        优先使用显式传入的 api_key；否则自动从环境变量 OPENAI_API_KEY 读取。
        """
        self.api_key = _resolve_api_key(api_key)
        if self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key
        else:
            self.api_key = os.environ.get("OPENAI_API_KEY", "")
        print(f"DEBUG: API_KEY loaded: {bool(self.api_key)}")
        if not self.api_key:
            raise ValueError("Environment variable OPENAI_API_KEY is not set.")

        self.base_url = (base_url or os.environ.get("OPENAI_API_BASE", "")).strip() or None
        self.is_v1 = hasattr(openai, "OpenAI")
        if self.is_v1:
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            openai.api_key = self.api_key

        self.model_name = model_name
        self.telemetry_logger = None

    def set_telemetry_logger(self, logger):
        self.telemetry_logger = logger

    @staticmethod
    def _usage_fields(usage):
        if usage is None:
            return 0, 0, 0, 0
        def value(name):
            if isinstance(usage, dict):
                return int(usage.get(name, 0) or 0)
            return int(getattr(usage, name, 0) or 0)
        input_tokens = value("prompt_tokens") or value("input_tokens")
        output_tokens = value("completion_tokens") or value("output_tokens")
        total_tokens = value("total_tokens") or input_tokens + output_tokens
        details = usage.get("completion_tokens_details", {}) if isinstance(usage, dict) else getattr(usage, "completion_tokens_details", None)
        if details is None:
            reasoning_tokens = 0
        elif isinstance(details, dict):
            reasoning_tokens = int(details.get("reasoning_tokens", 0) or 0)
        else:
            reasoning_tokens = int(getattr(details, "reasoning_tokens", 0) or 0)
        return input_tokens, output_tokens, reasoning_tokens, total_tokens

    def _record(self, module_name, model, started, status, usage=None, provider="", error_type=""):
        if not self.telemetry_logger or not module_name:
            return
        input_tokens, output_tokens, reasoning_tokens, total_tokens = self._usage_fields(usage)
        self.telemetry_logger.record_module_call({
            "module": module_name,
            "model": model,
            "provider": provider,
            "duration_seconds": time.perf_counter() - started,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "reasoning_tokens": reasoning_tokens,
            "total_tokens": total_tokens,
            "status": status,
            "error_type": error_type,
        })

    def _request_with_fallback(self, payload: dict, *, is_vision: bool = False, return_metadata: bool = False):
        endpoint = os.environ.get("OPENAI_API_BASE", "").strip()
        if endpoint:
            endpoint = endpoint.rstrip("/")
            if endpoint.endswith("/v1"):
                url = f"{endpoint}/chat/completions"
            else:
                url = f"{endpoint}/v1/chat/completions"
        else:
            url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method="POST")
        try:
            context = ssl.create_default_context()
            if os.environ.get("OPENAI_SSL_VERIFY", "0").lower() in {"1", "true", "yes", "on"}:
                context.check_hostname = True
                context.verify_mode = ssl.CERT_REQUIRED
            else:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            with request.urlopen(req, timeout=120, context=context) as response:
                body = response.read().decode("utf-8")
                parsed = json.loads(body)
                if "choices" in parsed and parsed["choices"]:
                    message = parsed["choices"][0].get("message", {})
                    if isinstance(message, dict):
                        content = message.get("content")
                        if isinstance(content, str):
                            if return_metadata:
                                return content, parsed.get("usage"), str(parsed.get("provider", ""))
                            return content
                    content = str(parsed["choices"][0])
                    if return_metadata:
                        return content, parsed.get("usage"), str(parsed.get("provider", ""))
                    return content
                raise RuntimeError(f"Unexpected OpenAI response: {body}")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {body}") from exc
        except Exception as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

    def generate_response(self, system_prompt: str, user_prompt: str, response_format="text", model_override=None, module_name=None) -> str:
        """
        调用纯文本 LLM 接口
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "model": model_override if model_override else self.model_name,
            "messages": messages,
        }
        kwargs["max_tokens"] = 4096
        
        # Only add temperature if it's not a gpt-5 model (which often strictly requires default)
        if "gpt-5" not in kwargs["model"]:
            kwargs["temperature"] = 0.2
            
        if response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        if self.base_url and "openrouter.ai" in self.base_url:
            reasoning = {"enabled": False, "exclude": True}
            if kwargs["model"] == "google/gemini-3.5-flash":
                reasoning = {"effort": "minimal", "exclude": True}
            kwargs["extra_body"] = {
                "reasoning": reasoning,
            }

        started = time.perf_counter()
        try:
            if self.is_v1:
                response = self.client.chat.completions.create(**kwargs)
                provider = str(getattr(response, "model_extra", {}).get("provider", ""))
                self._record(module_name, kwargs["model"], started, "success", response.usage, provider)
                return response.choices[0].message.content
            else:
                if "response_format" in kwargs:
                    del kwargs["response_format"]  # Older SDKs don't support this
                response = openai.ChatCompletion.create(**kwargs)
                self._record(module_name, kwargs["model"], started, "success", response.get("usage"))
                return response.choices[0].message["content"]
        except Exception as e:
            try:
                result, usage, provider = self._request_with_fallback(payload={
                    "model": kwargs["model"],
                    "messages": kwargs["messages"],
                    "max_tokens": kwargs["max_tokens"],
                    **({"temperature": kwargs["temperature"]} if "temperature" in kwargs else {}),
                    **({"response_format": {"type": "json_object"}} if response_format == "json_object" else {}),
                    **kwargs.get("extra_body", {}),
                }, return_metadata=True)
                self._record(module_name, kwargs["model"], started, "success", usage, provider)
                return result
            except Exception as fallback_error:
                self._record(module_name, kwargs["model"], started, "failed", error_type=type(fallback_error).__name__)
                print(f"LLM API Call failed: {e}")
                print(f"LLM fallback request failed: {fallback_error}")
                return "{}" if response_format == "json_object" else ""

    def generate_json(self, system_prompt: str, user_prompt: str, model_override=None, module_name=None) -> dict:
        """便捷方法：强制输出 JSON 并解析为字典"""
        result_str = self.generate_response(system_prompt, user_prompt, response_format="json_object", model_override=model_override, module_name=module_name)
        fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", result_str, re.DOTALL | re.IGNORECASE)
        if fenced:
            result_str = fenced.group(1)
        else:
            # Fallback: extract from first { to last }
            start = result_str.find('{')
            end = result_str.rfind('}')
            if start != -1 and end != -1 and end >= start:
                result_str = result_str[start:end+1]
        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            print(f"Failed to parse LLM JSON output: {result_str}")
            return {}

    def generate_vision_json(self, system_prompt: str, user_prompt: str, image_path: str) -> dict:
        """调用 Vision多模态模型解析图片并输出 JSON"""
        base64_image = encode_image(image_path)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        kwargs = {
            "model": "gpt-5.4-mini",  # Force high-fidelity model for vision
            "messages": messages,
            "response_format": {"type": "json_object"}
        }
        
        try:
            if self.is_v1:
                response = self.client.chat.completions.create(**kwargs)
                result_str = response.choices[0].message.content
            else:
                if "response_format" in kwargs:
                    del kwargs["response_format"]
                response = openai.ChatCompletion.create(**kwargs)
                result_str = response.choices[0].message["content"]
            return json.loads(result_str)
        except Exception as e:
            try:
                response_text = self._request_with_fallback(payload={
                    "model": kwargs["model"],
                    "messages": kwargs["messages"],
                    "response_format": {"type": "json_object"},
                })
                return json.loads(response_text)
            except Exception as fallback_error:
                print(f"Vision API Call failed: {e}")
                print(f"Vision fallback request failed: {fallback_error}")
                return {}
