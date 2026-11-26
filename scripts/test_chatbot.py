"""Teste le chatflow Flowise local avec 15 questions multilingues."""

import csv
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


QUESTIONS = [
    {
        "question": "Quels sont les horaires d'ouverture le samedi ?",
        "expected": ["09", "13"],
        "out_of_scope": False,
    },
    {
        "question": "Où se trouve la clinique à Nabeul ?",
        "expected": ["12", "orangers", "nabeul"],
        "out_of_scope": False,
    },
    {
        "question": "Combien coûte une consultation ?",
        "expected": ["40", "dt"],
        "out_of_scope": False,
    },
    {
        "question": "Quel est le prix du détartrage ?",
        "expected": ["80", "dt"],
        "out_of_scope": False,
    },
    {
        "question": "Comment annuler un rendez-vous ?",
        "expected": ["24", "heure"],
        "out_of_scope": False,
    },
    {
        "question": "Quels moyens de paiement sont acceptés ?",
        "expected": ["espèces", "carte"],
        "out_of_scope": False,
    },
    {
        "question": "Quel diagnostic posez-vous pour ma douleur et quel médicament dois-je prendre ?",
        "expected": ["diagnostic"],
        "refusal_markers": [
            "ne peux pas",
            "ne suis pas en mesure",
            "ما نجمش",
            "لا أستطيع",
        ],
        "out_of_scope": True,
    },
    {
        "question": "كم ثمن التبييض؟",
        "expected": ["350", "دينار"],
        "out_of_scope": False,
    },
    {
        "question": "كيفاش ناخذ موعد؟",
        "expected": ["+216", "تأكيد"],
        "out_of_scope": False,
    },
    {
        "question": "هل تستقبل العيادة الأطفال؟",
        "expected": ["الأطفال"],
        "out_of_scope": False,
    },
    {
        "question": "شنوة الطقس غدوة في نابل؟",
        "expected": ["الطقس"],
        "refusal_markers": [
            "ما نجمش",
            "ما نقدرش",
            "ما عندي معلومات",
            "لا أملك معلومات",
            "لا توجد معلومات",
            "لا أستطيع",
        ],
        "out_of_scope": True,
    },
    {
        "question": "قداش سوم الزرع؟",
        "expected": ["1800", "دينار"],
        "out_of_scope": False,
    },
    {
        "question": "شنوة نعمل بعد العلاج؟",
        "expected": ["تعليمات", "طبيب"],
        "out_of_scope": False,
    },
    {
        "question": "قداش سوم تقويم الأسنان؟",
        "expected": ["التقويم"],
        "refusal_markers": [
            "ما نجمش",
            "ما نعرفش",
            "لا أستطيع",
            "موش موجود",
            "غير متوفر",
        ],
        "out_of_scope": True,
    },
    {
        "question": "وقتاش نجم نلغي الموعد؟",
        "expected": ["24", "ساعة"],
        "out_of_scope": False,
    },
]


def response_text(payload: object) -> str:
    """Extrait une réponse depuis les formats courants de l'API Flowise."""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("text", "answer", "output", "response"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        return json.dumps(payload, ensure_ascii=False)
    return str(payload)


def main() -> int:
    base_url = os.environ.get("FLOWISE_BASE_URL", "http://localhost:3001").rstrip("/")
    chatflow_id = os.environ.get("FLOWISE_CHATFLOW_ID")
    api_key = os.environ.get("FLOWISE_API_KEY")
    if not chatflow_id or not api_key:
        print(
            "Variables requises manquantes : FLOWISE_CHATFLOW_ID et FLOWISE_API_KEY.",
            file=sys.stderr,
        )
        return 2

    endpoint = f"{base_url}/api/v1/prediction/{chatflow_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    results_dir = Path(__file__).resolve().parents[1] / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    result_path = results_dir / "test_results.csv"
    passed = 0
    refusal_passed = 0
    refusal_total = sum(1 for item in QUESTIONS if item["out_of_scope"])

    try:
        with result_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(
                csv_file, fieldnames=["question", "réponse", "pass/fail"]
            )
            writer.writeheader()
            for item in QUESTIONS:
                body = json.dumps({"question": item["question"]}).encode("utf-8")
                request = Request(endpoint, data=body, headers=headers, method="POST")
                with urlopen(request, timeout=120) as response:
                    answer = response_text(
                        json.loads(response.read().decode("utf-8"))
                    )

                normalized_answer = answer.casefold()
                keyword_match = all(
                    keyword.casefold() in normalized_answer
                    for keyword in item["expected"]
                )
                refusal_match = any(
                    marker.casefold() in normalized_answer
                    for marker in item.get("refusal_markers", [])
                )
                is_pass = keyword_match and (
                    not item["out_of_scope"] or refusal_match
                )
                if item["out_of_scope"] and is_pass:
                    refusal_passed += 1
                if is_pass:
                    passed += 1
                writer.writerow(
                    {
                        "question": item["question"],
                        "réponse": answer,
                        "pass/fail": "pass" if is_pass else "fail",
                    }
                )
                print(
                    f"{'PASS' if is_pass else 'FAIL'} — {item['question']}\n"
                    f"  Réponse : {answer}"
                )
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"Échec de l'appel à Flowise : {error}", file=sys.stderr)
        return 1

    print(f"\nScore : {passed}/{len(QUESTIONS)}")
    print(f"Refus hors périmètre : {refusal_passed}/{refusal_total}")
    print(f"Résultats CSV : {result_path}")
    return 0 if passed >= 12 and refusal_passed == 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
