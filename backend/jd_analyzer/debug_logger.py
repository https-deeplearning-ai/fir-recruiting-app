"""
Debug Logger for JD Analyzer Pipeline

Provides colored, structured logging for debugging the JD search pipeline:
JD Text -> Parsed Requirements -> LLM Query Generation -> Elasticsearch DSL -> CoreSignal API -> Candidates

Enable logging by setting environment variable: JD_DEBUG=1
Logs are written to console and backend/logs/debug.log
"""

import os
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class DebugLogger:
    """
    Structured logger for JD Analyzer pipeline debugging

    Usage:
        from jd_analyzer.debug_logger import debug_log

        debug_log.jd_parse("Parsing JD text...", jd_text="Some job description")
        debug_log.llm_prompt("Claude Haiku 4.5", prompt="Generate query...")
        debug_log.llm_response("Claude Haiku 4.5", response={"query": {...}})
        debug_log.coresignal_api("Searching CoreSignal", query={...}, page=1)
        debug_log.error("LLM parsing failed", exception=e)
    """

    def __init__(self):
        self.enabled = os.getenv('JD_DEBUG', '0') == '1'
        self.log_file = None

        if self.enabled:
            # Create logs directory if it doesn't exist
            log_dir = Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / 'debug.log'

            # Write session header
            self._write(f"\n{'='*80}\n")
            self._write(f"JD Analyzer Debug Session - {datetime.now().isoformat()}\n")
            self._write(f"{'='*80}\n\n")

    def _write(self, message: str, color: str = ''):
        """Write message to both console and log file"""
        if not self.enabled:
            return

        # Console output with color
        if color:
            print(f"{color}{message}{Colors.ENDC}", flush=True)
        else:
            print(message, flush=True)

        # File output without color codes
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message + '\n')

    def _truncate(self, text: str, max_length: int = 500, preview_only: bool = False) -> str:
        """Truncate long text with ellipsis"""
        if not text:
            return "None"

        if len(text) <= max_length:
            return text

        if preview_only:
            return text[:max_length] + f"... ({len(text)} chars total)"

        return text[:max_length] + "..."

    def _pretty_json(self, data: Any, max_length: int = 2000) -> str:
        """Pretty-print JSON with optional truncation"""
        try:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            return self._truncate(json_str, max_length)
        except (TypeError, ValueError):
            return str(data)

    def jd_parse(self, message: str, jd_text: Optional[str] = None,
                 requirements: Optional[Dict] = None, success: bool = True):
        """Log JD parsing step"""
        section = f"{Colors.OKCYAN}[JD_PARSE]{Colors.ENDC}"

        if success:
            self._write(f"{section} {Colors.OKGREEN}✓{Colors.ENDC} {message}", Colors.OKCYAN)
        else:
            self._write(f"{section} {Colors.FAIL}✗{Colors.ENDC} {message}", Colors.OKCYAN)

        if jd_text:
            self._write(f"  JD Text ({len(jd_text)} chars):")
            self._write(f"  {self._truncate(jd_text, 500, preview_only=True)}")

        if requirements:
            self._write(f"  Parsed Requirements:")
            role = requirements.get('role_title', 'N/A')
            seniority = requirements.get('seniority_level', 'N/A')
            skills_count = len(requirements.get('technical_skills', []))
            must_have_count = len(requirements.get('must_have', []))
            exp = requirements.get('experience_years', {})
            exp_str = f"{exp.get('minimum', 'N/A')}-{exp.get('preferred', 'N/A')} years"

            self._write(f"    Role: {role} | Seniority: {seniority}")
            self._write(f"    Experience: {exp_str} | Skills: {skills_count} | Must-have: {must_have_count}")

        self._write("")  # Blank line

    def llm_prompt(self, model: str, prompt: Optional[str] = None,
                   requirements: Optional[Dict] = None, temperature: float = 0.0,
                   max_tokens: int = 4096):
        """Log LLM prompt generation"""
        section = f"{Colors.OKBLUE}[LLM_PROMPT]{Colors.ENDC}"

        self._write(f"{section} {model} generating query", Colors.OKBLUE)
        self._write(f"  Model: {model} | Temp: {temperature} | Max Tokens: {max_tokens}")

        if requirements:
            self._write(f"  Requirements (abbreviated):")
            abbrev = {
                'role_title': requirements.get('role_title', 'N/A'),
                'seniority_level': requirements.get('seniority_level', 'N/A'),
                'technical_skills_count': len(requirements.get('technical_skills', [])),
                'location': requirements.get('location', 'N/A'),
                'experience_years': requirements.get('experience_years', {})
            }
            self._write(f"    {self._pretty_json(abbrev, 300)}")

        if prompt:
            self._write(f"  Prompt preview ({len(prompt)} chars):")
            self._write(f"    {self._truncate(prompt, 300)}")

        self._write("")

    def llm_response(self, model: str, response: Optional[str] = None,
                    parsed_query: Optional[Dict] = None, success: bool = True,
                    error: Optional[str] = None):
        """Log LLM response"""
        section = f"{Colors.OKBLUE}[LLM_RESPONSE]{Colors.ENDC}"

        if success:
            self._write(f"{section} {Colors.OKGREEN}✓{Colors.ENDC} {model} responded", Colors.OKBLUE)
        else:
            self._write(f"{section} {Colors.FAIL}✗{Colors.ENDC} {model} failed", Colors.OKBLUE)

        if error:
            self._write(f"  Error: {error}")

        if response:
            self._write(f"  Raw Response ({len(response)} chars):")
            self._write(f"    {self._truncate(response, 800)}")

        if parsed_query:
            self._write(f"  Parsed Query:")
            # Count complexity
            must_count = len(parsed_query.get('bool', {}).get('must', []))
            should_count = len(parsed_query.get('bool', {}).get('should', []))
            self._write(f"    Complexity: {must_count} must clauses, {should_count} should clauses")
            self._write(f"    {self._pretty_json(parsed_query, 1500)}")

        self._write("")

    def query_build(self, message: str, query: Optional[Dict] = None, success: bool = True):
        """Log query building step"""
        section = f"{Colors.WARNING}[QUERY_BUILD]{Colors.ENDC}"

        if success:
            self._write(f"{section} {Colors.OKGREEN}✓{Colors.ENDC} {message}", Colors.WARNING)
        else:
            self._write(f"{section} {Colors.FAIL}✗{Colors.ENDC} {message}", Colors.WARNING)

        if query:
            self._write(f"  Query Structure:")
            self._write(f"    {self._pretty_json(query, 1500)}")

        self._write("")

    def coresignal_api(self, message: str, query: Optional[Dict] = None,
                      page: Optional[int] = None, response: Optional[Dict] = None,
                      total_found: Optional[int] = None, profiles_count: Optional[int] = None,
                      first_profile: Optional[Dict] = None, success: bool = True,
                      error_status: Optional[int] = None, error_body: Optional[str] = None):
        """Log CoreSignal API call"""
        section = f"{Colors.HEADER}[CORESIGNAL_API]{Colors.ENDC}"

        if success:
            self._write(f"{section} {Colors.OKGREEN}✓{Colors.ENDC} {message}", Colors.HEADER)
        else:
            self._write(f"{section} {Colors.FAIL}✗{Colors.ENDC} {message}", Colors.HEADER)

        if page:
            self._write(f"  Page: {page}")

        if query:
            self._write(f"  Query:")
            self._write(f"    {self._pretty_json(query, 1000)}")

        if total_found is not None:
            self._write(f"  Results: {total_found} candidates found")

        if profiles_count is not None:
            self._write(f"  Profiles in response: {profiles_count}")

        if first_profile:
            name = first_profile.get('full_name', 'N/A')
            title = first_profile.get('active_experience_title') or first_profile.get('headline', 'N/A')
            exp_months = first_profile.get('total_experience_duration_months', 0)
            exp_years = round(exp_months / 12, 1) if exp_months else 0
            self._write(f"  First Profile: {name} | {title} | {exp_years} years exp")

        if error_status:
            self._write(f"  HTTP Status: {error_status}")

        if error_body:
            self._write(f"  Error Response:")
            self._write(f"    {self._truncate(error_body, 500)}")

        self._write("")

    def error(self, message: str, exception: Optional[Exception] = None,
             context: Optional[Dict] = None, raw_data: Optional[str] = None):
        """Log error with full context"""
        section = f"{Colors.FAIL}[ERROR]{Colors.ENDC}"

        self._write(f"{section} {message}", Colors.FAIL)

        if exception:
            self._write(f"  Exception: {type(exception).__name__}: {str(exception)}")
            self._write(f"  Traceback:")
            tb_lines = traceback.format_tb(exception.__traceback__)
            for line in tb_lines:
                self._write(f"    {line.strip()}")

        if context:
            self._write(f"  Context:")
            self._write(f"    {self._pretty_json(context, 500)}")

        if raw_data:
            self._write(f"  Raw Data ({len(raw_data)} chars):")
            self._write(f"    {self._truncate(raw_data, 500)}")

        self._write("")

    def info(self, message: str, data: Optional[Any] = None):
        """Log general information"""
        section = f"[INFO]"

        self._write(f"{section} {message}")

        if data:
            if isinstance(data, (dict, list)):
                self._write(f"  {self._pretty_json(data, 500)}")
            else:
                self._write(f"  {str(data)}")

        self._write("")


# Global singleton instance
debug_log = DebugLogger()
