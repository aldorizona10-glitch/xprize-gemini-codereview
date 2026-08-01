"""
CodeLens AI - Gemini-Powered Code Review Engine
Uses Google Gemini 2.0 Flash for intelligent code analysis
"""
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


REVIEW_PROMPT = """You are CodeLens AI, an expert code reviewer. Analyze the following code and provide a structured review.

**Code Language:** {language}
**Code to Review:**
```{language}
{code}
```

{context}

Provide your review as a JSON object with this exact structure:
{{
  "summary": "2-3 sentence overall assessment",
  "score": <number 1-100>,
  "issues": [
    {{
      "severity": "critical|warning|info|style",
      "line": <line_number_or_null>,
      "title": "Short issue title",
      "description": "Detailed explanation",
      "suggestion": "How to fix it"
    }}
  ],
  "strengths": ["List of things done well"],
  "recommendations": ["Top 3 improvement suggestions"],
  "security": {{
    "score": <number 1-100>,
    "findings": ["Any security concerns"]
  }},
  "performance": {{
    "score": <number 1-100>,
    "findings": ["Any performance concerns"]
  }}
}}

Be thorough but constructive. Focus on actionable feedback."""


class GeminiReviewer:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model
        self._configured = False
        if HAS_GEMINI and api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            self._configured = True

    async def review_code(
        self,
        code: str,
        language: str = "python",
        context: str = "",
        review_id: Optional[str] = None
    ) -> dict:
        if not review_id:
            review_id = hashlib.md5(
                f"{code}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:8]

        if not self._configured:
            return self._demo_review(code, language, review_id)

        try:
            ctx = f"**Additional Context:** {context}" if context else ""
            prompt = REVIEW_PROMPT.format(
                language=language, code=code, context=ctx
            )
            response = await self.model.generate_content_async(prompt)
            text = response.text

            # Extract JSON from response
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            review_data = json.loads(text.strip())
            review_data["review_id"] = review_id
            review_data["timestamp"] = datetime.now(timezone.utc).isoformat()
            review_data["language"] = language
            review_data["lines_reviewed"] = len(code.strip().split("\n"))
            review_data["powered_by"] = "Google Gemini 2.0 Flash"
            return review_data

        except Exception as e:
            return {
                "review_id": review_id,
                "error": str(e),
                "summary": "Review failed - falling back to demo mode",
                **self._demo_review(code, language, review_id)
            }

    def _demo_review(self, code: str, language: str, review_id: str) -> dict:
        lines = code.strip().split("\n")
        num_lines = len(lines)

        issues = []
        # Simple heuristic analysis for demo
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if "eval(" in stripped or "exec(" in stripped:
                issues.append({
                    "severity": "critical",
                    "line": i,
                    "title": "Dangerous code execution",
                    "description": f"Use of eval/exec detected on line {i}. This can lead to code injection.",
                    "suggestion": "Use ast.literal_eval() for safe evaluation or refactor logic."
                })
            if "password" in stripped.lower() and "=" in stripped and ("'" in stripped or '"' in stripped):
                issues.append({
                    "severity": "critical",
                    "line": i,
                    "title": "Hardcoded credential",
                    "description": "Possible hardcoded password detected.",
                    "suggestion": "Use environment variables or a secrets manager."
                })
            if len(stripped) > 120:
                issues.append({
                    "severity": "style",
                    "line": i,
                    "title": "Line too long",
                    "description": f"Line {i} exceeds 120 characters ({len(stripped)} chars).",
                    "suggestion": "Break into multiple lines for readability."
                })
            if stripped.startswith("except:") or stripped.startswith("except Exception:"):
                issues.append({
                    "severity": "warning",
                    "line": i,
                    "title": "Broad exception handling",
                    "description": "Catching all exceptions hides bugs.",
                    "suggestion": "Catch specific exceptions instead."
                })
            if "TODO" in stripped or "FIXME" in stripped or "HACK" in stripped:
                issues.append({
                    "severity": "info",
                    "line": i,
                    "title": "Unresolved TODO/FIXME",
                    "description": f"Found marker comment: {stripped[:60]}",
                    "suggestion": "Address or track this in your issue tracker."
                })

        if not issues:
            issues.append({
                "severity": "info",
                "line": None,
                "title": "No major issues found",
                "description": "The code looks clean! Minor improvements may still be possible.",
                "suggestion": "Consider adding type hints and docstrings."
            })

        score = max(30, 100 - len(issues) * 8)
        sec_score = 100 if not any(i["severity"] == "critical" for i in issues) else 45
        perf_score = max(60, 95 - num_lines // 10)

        return {
            "review_id": review_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "language": language,
            "lines_reviewed": num_lines,
            "score": score,
            "summary": f"Reviewed {num_lines} lines of {language} code. Found {len(issues)} issue(s). Overall quality: {'Good' if score > 70 else 'Needs attention'}.",
            "issues": issues,
            "strengths": [
                "Code structure is generally clear",
                "Naming conventions are reasonable",
                "Logic flow is followable"
            ],
            "recommendations": [
                "Add comprehensive docstrings and type hints",
                "Implement unit tests for critical paths",
                "Consider using a linter (e.g., ruff, eslint)"
            ],
            "security": {
                "score": sec_score,
                "findings": [i["title"] for i in issues if i["severity"] == "critical"] or ["No critical security issues"]
            },
            "performance": {
                "score": perf_score,
                "findings": ["Consider profiling hot paths", "Review data structure choices"]
            },
            "powered_by": "CodeLens AI (Demo Mode)"
        }
