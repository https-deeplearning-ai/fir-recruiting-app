"""
Session Logger for Domain Company Candidate Search

Provides comprehensive logging for all stages of the candidate search pipeline:
- JSON logs (structured data)
- TXT logs (human-readable)
- JSONL logs (streaming, one line per event)

Each search session gets its own directory with timestamped logs.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class SessionLogger:
    """
    Manages logging for a single candidate search session.

    Creates a session directory and provides methods to write:
    - JSON files (structured data)
    - TXT files (human-readable summaries)
    - JSONL files (streaming logs, one JSON object per line)
    """

    def __init__(self, session_id: Optional[str] = None, base_dir: Optional[str] = None):
        """
        Initialize session logger.

        Args:
            session_id: Optional session ID (generates one if not provided)
            base_dir: Optional base directory for logs (defaults to backend/logs/domain_search_sessions/)
        """
        self.session_id = session_id or self._generate_session_id()

        # Set base directory
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Default: backend/logs/domain_search_sessions/
            backend_dir = Path(__file__).parent.parent
            self.base_dir = backend_dir / "logs" / "domain_search_sessions"

        # Create session directory
        self.session_dir = self.base_dir / self.session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Track created files
        self.log_files = []

        # Write session metadata on creation
        self._log_session_metadata()

    def _generate_session_id(self) -> str:
        """Generate unique session ID with timestamp."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"sess_{timestamp}_{short_uuid}"

    def _log_session_metadata(self):
        """Write initial session metadata file."""
        metadata = {
            "session_id": self.session_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "log_directory": str(self.session_dir),
            "status": "initialized"
        }
        self.log_json("00_session_metadata.json", metadata)

    def log_json(self, filename: str, data: Dict[str, Any]):
        """
        Write JSON log file (overwrites if exists).

        Args:
            filename: Name of log file (e.g., "01_company_discovery.json")
            data: Dictionary to write as JSON
        """
        filepath = self.session_dir / filename

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.log_files.append(filename)
        print(f"✓ Log: {filepath.relative_to(Path.cwd())}")

    def log_text(self, filename: str, content: str):
        """
        Write human-readable text log file (overwrites if exists).

        Args:
            filename: Name of log file (e.g., "01_company_discovery_debug.txt")
            content: Text content to write
        """
        filepath = self.session_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        self.log_files.append(filename)
        print(f"✓ Log: {filepath.relative_to(Path.cwd())}")

    def log_jsonl(self, filename: str, data: Dict[str, Any]):
        """
        Append JSON object as single line to JSONL file (for streaming logs).

        Args:
            filename: Name of JSONL file (e.g., "03_collection_progress.jsonl")
            data: Dictionary to append as JSON line
        """
        filepath = self.session_dir / filename

        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

        # Only log file creation once
        if filename not in self.log_files:
            self.log_files.append(filename)
            print(f"✓ Streaming log: {filepath.relative_to(Path.cwd())}")

    def log_stage(self, stage_num: int, stage_name: str, data: Dict[str, Any], debug_text: Optional[str] = None):
        """
        Convenience method to log both JSON and TXT for a stage.

        Args:
            stage_num: Stage number (1-5)
            stage_name: Stage name (e.g., "company_discovery")
            data: Structured data to log as JSON
            debug_text: Optional human-readable text to log
        """
        # Add standard metadata
        if "stage" not in data:
            data["stage"] = stage_name
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Write JSON log
        json_filename = f"{stage_num:02d}_{stage_name}.json"
        self.log_json(json_filename, data)

        # Write TXT log if provided
        if debug_text:
            txt_filename = f"{stage_num:02d}_{stage_name}_debug.txt"
            self.log_text(txt_filename, debug_text)

    def get_log_path(self, filename: str) -> Path:
        """Get full path for a log file."""
        return self.session_dir / filename

    def list_log_files(self) -> List[str]:
        """Return list of all log files in session directory."""
        return sorted([f.name for f in self.session_dir.iterdir() if f.is_file()])

    def read_log(self, filename: str) -> str:
        """Read and return contents of a log file."""
        filepath = self.session_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filename}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def update_session_status(self, status: str, metadata: Optional[Dict] = None):
        """
        Update session metadata with current status.

        Args:
            status: Status string (e.g., "completed", "failed", "in_progress")
            metadata: Optional additional metadata to merge
        """
        metadata_file = self.session_dir / "00_session_metadata.json"

        # Read existing metadata
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        # Update status
        data["status"] = status
        data["last_updated"] = datetime.utcnow().isoformat() + "Z"

        # Merge additional metadata
        if metadata:
            data.update(metadata)

        # Write back
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def __repr__(self):
        return f"SessionLogger(session_id={self.session_id}, dir={self.session_dir})"


# Utility functions for formatting logs

def format_company_list(companies: List[Dict[str, Any]]) -> str:
    """
    Format company list as human-readable text.

    Args:
        companies: List of company dicts with name, source, confidence

    Returns:
        Formatted text string
    """
    lines = []
    lines.append("DOMAIN COMPANY DISCOVERY RESULTS")
    lines.append("=" * 50)
    lines.append("")

    # Group by source
    by_source = {}
    for company in companies:
        source = company.get("source", "unknown")
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(company)

    lines.append(f"Total Found: {len(companies)} companies")
    lines.append("")
    lines.append("BY SOURCE:")
    for source, comps in by_source.items():
        lines.append(f"  {source.capitalize()}: {len(comps)}")
    lines.append("")

    # List all companies
    lines.append("FULL LIST (sorted by confidence):")
    sorted_companies = sorted(companies, key=lambda c: c.get("confidence", 0), reverse=True)
    for i, company in enumerate(sorted_companies, 1):
        name = company.get("name", "Unknown")
        source = company.get("source", "unknown")
        confidence = company.get("confidence", 0)
        lines.append(f"  {i:2d}. {name:30s} ({source}, {confidence:.2f})")

    return "\n".join(lines)


def format_preview_analysis(previews: List[Dict[str, Any]], domain_companies: List[str]) -> str:
    """
    Format preview search quality analysis as human-readable text.

    Args:
        previews: List of candidate preview dicts
        domain_companies: List of domain company names

    Returns:
        Formatted analysis text
    """
    lines = []
    lines.append("PREVIEW SEARCH QUALITY ANALYSIS")
    lines.append("=" * 50)
    lines.append(f"Total Candidates: {len(previews)}")
    lines.append("")

    # Analyze relevance
    domain_company_lower = [c.lower() for c in domain_companies]
    has_domain_exp = 0
    has_big_tech = 0
    current_only = 0

    big_tech = ["google", "meta", "amazon", "apple", "microsoft", "facebook", "netflix"]

    for candidate in previews:
        # Check work history for domain companies
        domain_match = False
        big_tech_match = False

        current_company = candidate.get("current_company", "").lower()
        headline = candidate.get("headline", "").lower()

        # Check if any domain company appears in headline or current company
        for dc in domain_company_lower:
            if dc in current_company or dc in headline:
                domain_match = True
                break

        # Check for big tech
        for bt in big_tech:
            if bt in headline:
                big_tech_match = True
                break

        if domain_match:
            has_domain_exp += 1
        if big_tech_match:
            has_big_tech += 1
        if domain_match and not big_tech_match:
            current_only += 1

    lines.append("RELEVANCE BREAKDOWN:")
    lines.append(f"  ✓ {has_domain_exp}/{len(previews)} ({has_domain_exp/len(previews)*100:.0f}%) worked at domain companies")
    lines.append(f"  ✓ {has_big_tech}/{len(previews)} ({has_big_tech/len(previews)*100:.0f}%) have Big Tech experience")
    lines.append(f"  ⚠ {current_only}/{len(previews)} ({current_only/len(previews)*100:.0f}%) only current company match")
    lines.append("")

    # Quality score
    quality_score = has_domain_exp / len(previews)
    if quality_score >= 0.7:
        quality_label = "EXCELLENT ✓✓"
    elif quality_score >= 0.5:
        quality_label = "GOOD ✓"
    elif quality_score >= 0.3:
        quality_label = "FAIR ⚠"
    else:
        quality_label = "POOR ✗"

    lines.append(f"QUALITY SCORE: {quality_score*100:.0f}% {quality_label}")

    if quality_score >= 0.5:
        lines.append("RECOMMENDATION: Proceed with full collection")
    else:
        lines.append("RECOMMENDATION: Refine query or adjust filters")

    lines.append("")
    lines.append("TOP 5 CANDIDATES:")
    for i, candidate in enumerate(previews[:5], 1):
        name = candidate.get("name", "Unknown")
        headline = candidate.get("headline", "")[:60]
        lines.append(f"  {i}. {name} - {headline}")

    return "\n".join(lines)


if __name__ == "__main__":
    # Test the logger
    logger = SessionLogger()
    print(f"Created session: {logger.session_id}")
    print(f"Log directory: {logger.session_dir}")

    # Test JSON logging
    logger.log_json("test.json", {"test": "data", "number": 123})

    # Test TXT logging
    logger.log_text("test.txt", "This is a test log file.\nWith multiple lines.")

    # Test JSONL logging
    logger.log_jsonl("test.jsonl", {"event": "started"})
    logger.log_jsonl("test.jsonl", {"event": "progress", "count": 10})
    logger.log_jsonl("test.jsonl", {"event": "completed"})

    # Test stage logging
    logger.log_stage(1, "test_stage", {"data": "test"}, debug_text="Test debug output")

    # List files
    print("\nLog files created:")
    for f in logger.list_log_files():
        print(f"  - {f}")

    # Update status
    logger.update_session_status("test_completed", {"test_key": "test_value"})

    print("\n✓ Session logger test completed successfully!")
