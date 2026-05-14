
import os
import json
import re
from groq import Groq
from prompts import SYSTEM_PROMPT, SUMMARIZE_PROMPT, QA_SYSTEM

class ClaudeClient:

    def __init__(self, api_key: str = ""):
        key = os.environ.get("GROQ_API_KEY", api_key)
        self.client = Groq(api_key=key)
        self.model  = "llama-3.3-70b-versatile"

    def summarize_report(self, report_text: str) -> dict:
        prompt = SUMMARIZE_PROMPT.format(report_text=report_text[:4000])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.3,
        )
        return self._parse_json(response.choices[0].message.content)

    def answer_question(self, report_text: str,
                        question: str, history: list) -> str:
        system = QA_SYSTEM.format(report_text=report_text[:3000])
        messages = [{"role": "system", "content": system}]
        for user_msg, assistant_msg in history:
            messages.append({"role": "user",      "content": user_msg})
            messages.append({"role": "assistant", "content": assistant_msg})
        messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def _parse_json(self, raw: str) -> dict:
        clean = re.sub(r'```json|```', '', raw).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass
        return {
            "report_type":         "General Medical Report",
            "summary_en":          raw[:500],
            "summary_ar":          "",
            "key_findings":        [],
            "red_flags":           [],
            "normal_findings":     [],
            "follow_up_suggested": False,
            "follow_up_reason":    "",
            "overall_status":      "Unknown"
        }
