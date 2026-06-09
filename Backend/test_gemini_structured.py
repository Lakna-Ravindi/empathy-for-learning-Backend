#!/usr/bin/env python3
"""Regression test for Gemini structured response handling."""

import sys
import types

dotenv_stub = types.ModuleType("dotenv")
dotenv_stub.load_dotenv = lambda *args, **kwargs: None
sys.modules.setdefault("dotenv", dotenv_stub)

from app.services.gemini_service import GeminiService


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


def run_case(name: str, stub_response: str, expected_error: str) -> None:
    service = GeminiService()
    service._call_gemini = lambda prompt, temperature=0.7, response_mime_type=None, user_message=None, safety=None, emotion=None, skill=None, chunk=None: FakeResponse(stub_response)

    result = service.generate_structured("Test prompt", [])

    assert "error" in result, f"{name}: expected error in result, got {result}"
    assert expected_error in result["error"], f"{name}: unexpected error {result['error']}"
    print(f"{name}: OK")


def test_retry_on_connection_error() -> None:
    service = GeminiService()
    
    class MockModels:
        def __init__(self):
            self.call_count = 0
            
        def generate_content(self, *args, **kwargs):
            self.call_count += 1
            if self.call_count == 1:
                raise ConnectionResetError("[WinError 10054] An existing connection was forcibly closed")
            return FakeResponse('{"response": "Recovered response"}')

    class MockClient:
        def __init__(self):
            self.models = MockModels()

    service.client = MockClient()
    
    import app.services.gemini_service as gemini_service_mod
    original_disabled = gemini_service_mod.GEMINI_DISABLED
    gemini_service_mod.GEMINI_DISABLED = False
    
    import time
    original_sleep = time.sleep
    time.sleep = lambda secs: None
    
    try:
        result = service.generate_structured("Test prompt", [])
        assert result == {"response": "Recovered response"}, f"Expected recovered response, got {result}"
        assert service.client.models.call_count == 2, f"Expected 2 calls, got {service.client.models.call_count}"
        print("retry-on-connection-error: OK")
    finally:
        time.sleep = original_sleep
        gemini_service_mod.GEMINI_DISABLED = original_disabled


def main() -> None:
    run_case("empty-response", "", "Empty structured response")
    run_case("plain-text-response", "I'm here to listen.", "JSON object")

    service = GeminiService()
    service._call_gemini = lambda prompt, temperature=0.7, response_mime_type=None, user_message=None, safety=None, emotion=None, skill=None, chunk=None: FakeResponse('{"response": "All good"}')
    result = service.generate_structured("Test prompt", [])
    assert result == {"response": "All good"}, result
    print("valid-json-response: OK")
    
    test_retry_on_connection_error()


if __name__ == "__main__":
    main()