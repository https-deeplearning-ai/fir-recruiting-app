"""
Shortlist Analyzer

Reverse-engineers implicit hiring criteria from a shortlist of candidates.
Discovers what recruiters actually value vs what the JD states.
"""

import csv
from collections import Counter
from typing import List, Dict, Any, Tuple

class ShortlistAnalyzer:
    """
    Analyzes a shortlist of candidates to discover implicit hiring criteria.

    Given a CSV of candidates (with LinkedIn URLs, titles, companies, locations),
    extracts patterns that reveal what recruiters actually prioritize.
    """

    def __init__(self, csv_path: str):
        """
        Initialize analyzer with candidate CSV.

        Args:
            csv_path: Path to CSV with columns: Profile URL, Current Title, Current Company, Location
        """
        self.csv_path = csv_path
        self.candidates = []
        self.patterns = {
            "locations": Counter(),
            "titles": Counter(),
            "companies": Counter(),
            "seniority_levels": {
                "c_suite": [],
                "vp_director": [],
                "senior_ic": [],
                "mid_level": []
            },
            "title_keywords": Counter(),
            "location_clusters": Counter()
        }

    def load_candidates(self) -> int:
        """
        Load candidates from CSV file.

        Returns:
            Number of candidates loaded
        """
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Flexible column name matching
                    linkedin_url = (
                        row.get("Profile URL") or
                        row.get("profile_url") or
                        row.get("LinkedIn URL") or
                        row.get("linkedin_url") or
                        ""
                    )

                    title = (
                        row.get("Current Title") or
                        row.get("current_title") or
                        row.get("Title") or
                        row.get("title") or
                        ""
                    )

                    company = (
                        row.get("Current Company") or
                        row.get("current_company") or
                        row.get("Company") or
                        row.get("company") or
                        ""
                    )

                    location = (
                        row.get("Location") or
                        row.get("location") or
                        ""
                    )

                    if linkedin_url:  # Only add if LinkedIn URL exists
                        self.candidates.append({
                            "linkedin_url": linkedin_url,
                            "title": title,
                            "company": company,
                            "location": location
                        })

            return len(self.candidates)

        except Exception as e:
            print(f"Error loading CSV: {e}")
            return 0

    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyze patterns in the candidate shortlist.

        Returns:
            Dictionary with discovered patterns:
            {
                "total_candidates": int,
                "location_distribution": Dict[str, int],
                "seniority_distribution": Dict[str, int],
                "top_companies": List[Tuple[str, int]],
                "title_keywords": Dict[str, int],
                "implicit_criteria": Dict[str, Any]
            }
        """
        if not self.candidates:
            return {}

        # Analyze locations
        for candidate in self.candidates:
            location = candidate["location"]
            self.patterns["locations"][location] += 1

            # Cluster locations
            cluster = self._cluster_location(location)
            self.patterns["location_clusters"][cluster] += 1

            # Analyze titles
            title = candidate["title"]
            self.patterns["titles"][title] += 1

            # Categorize by seniority
            seniority = self._categorize_seniority(title)
            self.patterns["seniority_levels"][seniority].append(candidate)

            # Extract title keywords
            keywords = self._extract_title_keywords(title)
            for keyword in keywords:
                self.patterns["title_keywords"][keyword] += 1

            # Analyze companies
            company = candidate["company"]
            self.patterns["companies"][company] += 1

        # Generate analysis summary
        total = len(self.candidates)
        return {
            "total_candidates": total,
            "location_distribution": dict(self.patterns["location_clusters"]),
            "seniority_distribution": {
                k: len(v) for k, v in self.patterns["seniority_levels"].items()
            },
            "top_companies": self.patterns["companies"].most_common(15),
            "title_keywords": dict(self.patterns["title_keywords"].most_common(10)),
            "implicit_criteria": self._infer_implicit_criteria()
        }

    def _cluster_location(self, location: str) -> str:
        """Cluster locations into major hubs"""
        location_lower = location.lower()

        bay_area_terms = [
            "san francisco", "bay area", "palo alto", "mountain view",
            "sunnyvale", "menlo park", "redwood city", "san mateo",
            "san jose", "los altos", "san carlos", "cupertino",
            "oakland", "berkeley", "fremont"
        ]
        seattle_terms = ["seattle", "bellevue", "redmond", "kirkland"]
        ny_terms = ["new york", "manhattan", "brooklyn", "nyc"]
        boston_terms = ["boston", "cambridge", "somerville"]

        if any(term in location_lower for term in bay_area_terms):
            return "San Francisco Bay Area"
        elif any(term in location_lower for term in seattle_terms):
            return "Greater Seattle Area"
        elif any(term in location_lower for term in ny_terms):
            return "New York"
        elif any(term in location_lower for term in boston_terms):
            return "Greater Boston"
        elif "united states" in location_lower:
            return "United States (remote)"
        else:
            return location

    def _categorize_seniority(self, title: str) -> str:
        """Categorize title by seniority level"""
        title_lower = title.lower()

        c_suite_keywords = ["ceo", "cto", "chief", "co-founder", "founder", "head of"]
        vp_director_keywords = ["vp", "vice president", "director"]
        senior_ic_keywords = ["staff", "principal", "senior", "lead", "research scientist"]

        if any(kw in title_lower for kw in c_suite_keywords):
            return "c_suite"
        elif any(kw in title_lower for kw in vp_director_keywords):
            return "vp_director"
        elif any(kw in title_lower for kw in senior_ic_keywords):
            return "senior_ic"
        else:
            return "mid_level"

    def _extract_title_keywords(self, title: str) -> List[str]:
        """Extract relevant keywords from title"""
        title_lower = title.lower()
        keywords_of_interest = [
            "ai", "ml", "voice", "speech", "llm", "nlp",
            "generative", "conversational", "agentic", "machine learning",
            "data", "platform", "infrastructure"
        ]

        found = []
        for keyword in keywords_of_interest:
            if keyword in title_lower:
                found.append(keyword)

        return found

    def _infer_implicit_criteria(self) -> Dict[str, Any]:
        """Infer implicit hiring criteria from patterns"""
        total = len(self.candidates)

        # Location preference
        top_location = self.patterns["location_clusters"].most_common(1)[0]
        location_pct = (top_location[1] / total) * 100

        # Seniority distribution
        c_suite_count = len(self.patterns["seniority_levels"]["c_suite"])
        c_suite_pct = (c_suite_count / total) * 100

        senior_ic_count = len(self.patterns["seniority_levels"]["senior_ic"])
        senior_ic_pct = (senior_ic_count / total) * 100

        # Company clustering (referral signal)
        top_companies = self.patterns["companies"].most_common(5)
        max_company_count = top_companies[0][1] if top_companies else 0
        referral_signal = max_company_count >= 3  # 3+ from same company suggests referrals

        return {
            "primary_location": top_location[0],
            "location_preference_strength": f"{location_pct:.1f}%",
            "seniority_flexibility": {
                "c_suite_preferred": c_suite_pct > 40,
                "accepts_senior_ic": senior_ic_pct > 15
            },
            "referral_driven_sourcing": referral_signal,
            "top_feeder_companies": [comp[0] for comp in top_companies[:5]]
        }

    def compare_to_jd(
        self,
        jd_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare shortlist patterns to stated JD requirements.

        Args:
            jd_requirements: Parsed JD from JDParser

        Returns:
            Dictionary of gaps between JD and reality:
            {
                "location_gap": {...},
                "seniority_gap": {...},
                "experience_gap": {...}
            }
        """
        if not self.candidates:
            return {}

        analysis = self.analyze_patterns()
        implicit = analysis["implicit_criteria"]

        gaps = {}

        # Location gap
        jd_location = jd_requirements.get("location", "")
        actual_location = implicit["primary_location"]
        if jd_location.lower() != actual_location.lower():
            gaps["location_gap"] = {
                "jd_states": jd_location,
                "reality": f"{implicit['location_preference_strength']} in {actual_location}",
                "insight": "Implicit geographic preference despite broader JD statement"
            }

        # Seniority gap
        jd_seniority = jd_requirements.get("seniority_level", "").lower()
        seniority_dist = analysis["seniority_distribution"]

        if "c-suite" in jd_seniority or "executive" in jd_seniority:
            ic_pct = (seniority_dist.get("senior_ic", 0) / analysis["total_candidates"]) * 100
            if ic_pct > 15:
                gaps["seniority_gap"] = {
                    "jd_states": f"C-Suite / Executive ({jd_seniority})",
                    "reality": f"{ic_pct:.1f}% are Senior ICs (not executives)",
                    "insight": "More flexible on seniority than JD suggests"
                }

        # Must-have vs nice-to-have gap
        jd_must_have = jd_requirements.get("must_have", [])
        jd_nice_to_have = jd_requirements.get("nice_to_have", [])

        # Check if "nice to have" items appear frequently in shortlist titles
        title_keyword_str = " ".join(analysis["title_keywords"].keys()).lower()
        for nice_item in jd_nice_to_have:
            nice_lower = nice_item.lower()
            # Extract key terms
            key_terms = [term for term in ["voice", "speech", "ai", "ml", "nlp"] if term in nice_lower]
            if key_terms and any(term in title_keyword_str for term in key_terms):
                gaps["nice_to_have_actually_required"] = {
                    "jd_states": f"Nice to have: {nice_item}",
                    "reality": f"Appears in {analysis['title_keywords']} candidate titles",
                    "insight": "Listed as 'nice to have' but appears to be hard requirement"
                }
                break

        return gaps

    def generate_report(self, jd_requirements: Dict[str, Any] = None) -> str:
        """
        Generate markdown report of shortlist analysis.

        Args:
            jd_requirements: Optional JD requirements for gap analysis

        Returns:
            Markdown-formatted report
        """
        analysis = self.analyze_patterns()

        report = f"# Shortlist Analysis Report\n\n"
        report += f"**Total Candidates:** {analysis['total_candidates']}\n\n"

        report += "## Location Distribution\n\n"
        for location, count in sorted(
            analysis["location_distribution"].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            pct = (count / analysis["total_candidates"]) * 100
            report += f"- {location}: {count} ({pct:.1f}%)\n"

        report += "\n## Seniority Distribution\n\n"
        for level, count in analysis["seniority_distribution"].items():
            pct = (count / analysis["total_candidates"]) * 100
            report += f"- {level.replace('_', ' ').title()}: {count} ({pct:.1f}%)\n"

        report += "\n## Top Companies\n\n"
        for company, count in analysis["top_companies"]:
            report += f"- {company}: {count}\n"

        report += "\n## Title Keywords\n\n"
        for keyword, count in analysis["title_keywords"].items():
            pct = (count / analysis["total_candidates"]) * 100
            report += f"- {keyword.upper()}: {count} ({pct:.1f}%)\n"

        report += "\n## Implicit Criteria\n\n"
        implicit = analysis["implicit_criteria"]
        report += f"- **Primary Location:** {implicit['primary_location']} ({implicit['location_preference_strength']})\n"
        report += f"- **Seniority Flexibility:** C-Suite preferred = {implicit['seniority_flexibility']['c_suite_preferred']}, Accepts Senior IC = {implicit['seniority_flexibility']['accepts_senior_ic']}\n"
        report += f"- **Referral-Driven:** {implicit['referral_driven_sourcing']}\n"
        report += f"- **Top Feeder Companies:** {', '.join(implicit['top_feeder_companies'])}\n"

        if jd_requirements:
            gaps = self.compare_to_jd(jd_requirements)
            if gaps:
                report += "\n## JD vs Reality Gaps\n\n"
                for gap_type, gap_data in gaps.items():
                    report += f"### {gap_type.replace('_', ' ').title()}\n"
                    report += f"- **JD States:** {gap_data['jd_states']}\n"
                    report += f"- **Reality:** {gap_data['reality']}\n"
                    report += f"- **Insight:** {gap_data['insight']}\n\n"

        return report
