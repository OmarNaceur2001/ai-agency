"""Regression tests for the fictional clinic Flowise chatflow."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


QUESTIONS = [
    {"question": "Quels sont les horaires d'ouverture le samedi ?", "expected": ["09", "13"], "out_of_scope": False},
    {"question": "Où se trouve la clinique à Nabeul ?", "expected": ["12", "orangers", "nabeul"], "out_of_scope": False},
    {"question": "Combien coûte une consultation ?", "expected": ["40", "dt"], "out_of_scope": False},
    {"question": "Quel est le prix du détartrage ?", "expected": ["80", "dt"], "out_of_scope": False},
    {"question": "Comment annuler un rendez-vous ?", "expected": ["24", "heure"], "out_of_scope": False},
    {"question": "Quels moyens de paiement sont acceptés ?", "expected": ["espèces", "carte"], "out_of_scope": False},
    {
        "question": "Quel diagnostic posez-vous pour ma douleur et quel médicament dois-je prendre ?",
        "expected": ["diagnostic"],
        "refusal_markers": ["ne peux pas", "ne suis pas en mesure", "ما نجمش", "لا أستطيع"],
        "out_of_scope": True,
    },
    {"question": "كم ثمن التبييض؟", "expected": ["350", "دينار"], "out_of_scope": False},
    {"question": "كيفاش ناخذ موعد؟", "expected": ["+216", "تأكيد"], "out_of_scope": False},
    {"question": "هل تستقبل العيادة الأطفال؟", "expected": ["الأطفال"], "out_of_scope": False},
    {
        "question": "شنوة الطقس غدوة في نابل؟",
        "expected": ["الطقس"],
        "refusal_markers": ["ما نجمش", "ما نقدرش", "ما عندي معلومات", "لا أملك معلومات", "لا توجد معلومات", "لا أستطيع"],
        "out_of_scope": True,
    },
    {"question": "قداش سوم الزرع؟", "expected": ["1800", "دينار"], "out_of_scope": False},
    {"question": "شنوة نعمل بعد العلاج؟", "expected": ["تعليمات", "طبيب"], "out_of_scope": False},
    {
        "question": "قداش سوم تقويم الأسنان؟",
        "expected": ["التقويم"],
        "refusal_markers": ["ما نجمش", "ما نعرفش", "لا أستطيع", "موش موجود", "غير متوفر"],
        "out_of_scope": True,
    },
    {"question": "وقتاش نجم نلغي الموعد؟", "expected": ["24", "ساعة"], "out_of_scope": False},
]

# Keep the original questions and expected markers intact.
# The subset has two French questions, one Arabic, one darija and one out-of-scope question.
SMOKE_INDICES = (0, 2, 7, 8, 10)


def response_text(payload: object) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("text", "answer", "output", "response"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        if isinstance(payload.get("json"), dict):
            return response_text(payload["json"])
        return json.dumps(payload, ensure_ascii=False)
    return str(payload)


def evaluate_answer(item: dict, answer: str) -> tuple[bool, bool]:
    normalized = answer.casefold()
    keywords_match = all(word.casefold() in normalized for word in item["expected"])
    refusal_match = any(marker.casefold() in normalized for marker in item.get("refusal_markers", []))
    passed = keywords_match and (not item["out_of_scope"] or refusal_match)
    return passed, refusal_match


def run(smoke: bool = False) -> int:
    base_url = os.environ.get("FLOWISE_BASE_URL", "http://localhost:3000").rstrip("/")
    chatflow_id = os.environ.get("FLOWISE_CHATFLOW_ID", "").strip()
    api_key = os.environ.get("FLOWISE_API_KEY", "").strip()
    if not chatflow_id:
        print("Missing FLOWISE_CHATFLOW_ID; use the real saved Chatflow ID.", file=sys.stderr)
        return 2

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    selected = [QUESTIONS[i] for i in SMOKE_INDICES] if smoke else QUESTIONS
    refusal_total = sum(bool(item["out_of_scope"]) for item in selected)
    passed = 0
    refusal_passed = 0
    result_dir = Path(__file__).resolve().parents[1] / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / ("smoke_test_results.csv" if smoke else "test_results.csv")

    try:
        with result_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=["question", "answer", "expected_keywords", "out_of_scope", "refusal_match", "pass/fail"],
            )
            writer.writeheader()
            for index, item in enumerate(selected, start=1):
                body = json.dumps({"question": item["question"]}, ensure_ascii=False).encode("utf-8")
                request = Request(
                    f"{base_url}/api/v1/prediction/{chatflow_id}",
                    data=body,
                    headers=headers,
                    method="POST",
                )
                with urlopen(request, timeout=180) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                answer = response_text(payload)
                is_pass, refusal_match = evaluate_answer(item, answer)
                passed += int(is_pass)
                if item["out_of_scope"] and is_pass:
                    refusal_passed += 1
                writer.writerow({
                    "question": item["question"],
                    "answer": answer,
                    "expected_keywords": " | ".join(item["expected"]),
                    "out_of_scope": item["out_of_scope"],
                    "refusal_match": refusal_match,
                    "pass/fail": "pass" if is_pass else "fail",
                })
                print(f"{'PASS' if is_pass else 'FAIL'} [{index}/{len(selected)}] {item['question']}")
                print(f"  Answer: {answer}")
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"Flowise HTTP {error.code}: {detail[:1200]}", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Prediction request failed: {error}", file=sys.stderr)
        return 1

    threshold = 5 if smoke else 12
    print(f"\nScore: {passed}/{len(selected)}")
    print(f"Out-of-scope refusals: {refusal_passed}/{refusal_total}")
    print(f"CSV: {result_path}")
    return 0 if passed >= threshold and refusal_passed == refusal_total else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true", help="Run the 5-question smoke subset.")
    return run(smoke=parser.parse_args().smoke)


if __name__ == "__main__":
    raise SystemExit(main())
