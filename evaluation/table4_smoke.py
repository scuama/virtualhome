"""Perform one non-benchmark JSON compatibility request per Table 4 model."""

import json

from agent.utils.llm_client import LLMClient
from evaluation.table4_configs import MODELS


def main() -> None:
    results = []
    for alias, model_id in MODELS.items():
        client = LLMClient(model_name=model_id)
        response = client.generate_json(
            "Return a JSON object only.",
            'Return exactly {"ok": true}.',
        )
        ok = response.get("ok") is True
        results.append({"model_alias": alias, "model_id": model_id, "ok": ok})
        print(f"{alias}: {'OK' if ok else 'FAILED'}")
    if not all(item["ok"] for item in results):
        raise SystemExit("One or more Table 4 model smoke requests failed")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
