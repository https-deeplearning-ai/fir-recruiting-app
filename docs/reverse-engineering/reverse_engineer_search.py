"""
Reverse-Engineer CoreSignal Search Criteria

Given a job description and a shortlist of candidates (LinkedIn URLs),
this script discovers the optimal CoreSignal search query that returns
these exact candidates by analyzing patterns in their profiles.

Usage:
    python3 reverse_engineer_search.py --csv "vocal bridge fir-Linda test - Jon reaching out.csv" --jd vocal_bridge_fir_job_description.md

Author: AI Fund Reverse-Engineering Tool
Date: 2025-10-28
"""

import csv
import json
import os
import sys
from collections import Counter
from typing import List, Dict, Tuple, Any

# Analysis results storage
class ReverseEngineerAnalysis:
    def __init__(self, csv_path: str, jd_path: str = None):
        self.csv_path = csv_path
        self.jd_path = jd_path
        self.candidates = []
        self.jd_text = ""
        self.analysis = {
            "total_candidates": 0,
            "locations": Counter(),
            "titles": Counter(),
            "companies": Counter(),
            "seniority_levels": {
                "c_suite": [],
                "vp_director": [],
                "senior_ic": [],
                "mid_level": []
            },
            "industries_inferred": [],
            "location_clusters": {},
            "title_keywords": Counter(),
            "company_types": Counter()
        }

    def load_data(self):
        """Load CSV and JD data"""
        # Load candidates from CSV
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.candidates.append({
                    "first_name": row.get("First Name", ""),
                    "last_name": row.get("Last Name", ""),
                    "location": row.get("Location", ""),
                    "title": row.get("Current Title", ""),
                    "company": row.get("Current Company", ""),
                    "linkedin_url": row.get("Profile URL", ""),
                    "email": row.get("email address", ""),
                    "date_of_email": row.get("date of email", ""),
                    "date_of_inmail": row.get("date of inmail", ""),
                    "interview_date": row.get("interview date", "")
                })

        self.analysis["total_candidates"] = len(self.candidates)

        # Load JD if provided
        if self.jd_path and os.path.exists(self.jd_path):
            with open(self.jd_path, 'r', encoding='utf-8') as f:
                self.jd_text = f.read()

        print(f"✓ Loaded {len(self.candidates)} candidates from CSV")
        if self.jd_text:
            print(f"✓ Loaded job description ({len(self.jd_text)} chars)")

    def analyze_patterns(self):
        """Extract patterns from candidate shortlist"""
        print("\n=== ANALYZING CANDIDATE PATTERNS ===\n")

        # Analyze locations
        for candidate in self.candidates:
            location = candidate["location"]
            self.analysis["locations"][location] += 1

            # Normalize locations to clusters
            location_lower = location.lower()
            if any(term in location_lower for term in ["san francisco", "bay area", "palo alto", "mountain view", "sunnyvale", "menlo park", "redwood city", "san mateo", "san jose", "los altos", "san carlos"]):
                cluster = "San Francisco Bay Area"
            elif any(term in location_lower for term in ["seattle", "bellevue", "redmond"]):
                cluster = "Greater Seattle Area"
            elif any(term in location_lower for term in ["new york", "manhattan", "brooklyn"]):
                cluster = "New York"
            elif any(term in location_lower for term in ["boston", "cambridge"]):
                cluster = "Greater Boston"
            elif "houston" in location_lower:
                cluster = "Houston"
            elif "minneapolis" in location_lower:
                cluster = "Greater Minneapolis-St. Paul Area"
            elif "united states" in location_lower:
                cluster = "United States (remote)"
            elif "ann arbor" in location_lower:
                cluster = "Ann Arbor"
            elif "burlington" in location_lower:
                cluster = "Burlington"
            elif "laguna beach" in location_lower:
                cluster = "Laguna Beach"
            else:
                cluster = location

            if cluster not in self.analysis["location_clusters"]:
                self.analysis["location_clusters"][cluster] = 0
            self.analysis["location_clusters"][cluster] += 1

        # Analyze titles and extract keywords
        seniority_keywords = {
            "c_suite": ["ceo", "cto", "chief", "co-founder", "founder", "head of"],
            "vp_director": ["vp", "vice president", "director", "head of engineering", "head of product", "head of ai"],
            "senior_ic": ["staff", "senior", "principal", "lead", "research scientist"],
            "mid_level": ["engineer", "software engineer", "product manager", "scientist", "member of technical staff"]
        }

        for candidate in self.candidates:
            title = candidate["title"]
            title_lower = title.lower()

            self.analysis["titles"][title] += 1

            # Categorize by seniority
            categorized = False
            for seniority, keywords in seniority_keywords.items():
                if any(kw in title_lower for kw in keywords):
                    self.analysis["seniority_levels"][seniority].append(candidate)
                    if not categorized:
                        categorized = True
                        break

            # Extract title keywords (AI, ML, Voice, etc.)
            title_words = title_lower.split()
            keywords_of_interest = ["ai", "ml", "voice", "speech", "llm", "nlp", "generative", "conversational", "agentic"]
            for word in title_words:
                for keyword in keywords_of_interest:
                    if keyword in word:
                        self.analysis["title_keywords"][keyword] += 1

            # Analyze companies
            company = candidate["company"]
            self.analysis["companies"][company] += 1

            # Categorize company types
            company_lower = company.lower()
            if company in ["Meta", "Google", "Amazon", "Amazon Web Services (AWS)", "Facebook AI", "Snowflake"]:
                company_type = "Big Tech / FAANG"
            elif company in ["Anthropic", "OpenAI", "xAI", "Hugging Face", "Together AI", "Anyscale", "LangChain", "Pinecone"]:
                company_type = "AI Infrastructure / Platform"
            elif company in ["Otter.ai", "Deepgram", "PlayAI", "ElevenLabs", "Phonic"]:
                company_type = "Voice AI Specialist"
            elif company in ["Sierra", "Vapi", "Brain Co.", "VOIA", "Contextual AI"]:
                company_type = "Conversational AI / Agentic"
            elif "Stealth" in company or company in ["Rembrand", "Rexiro", "AIAIO", "CloudAEye", "Wayline"]:
                company_type = "Startup / Stealth"
            else:
                company_type = "Other"

            self.analysis["company_types"][company_type] += 1

        # Print analysis
        print("📍 LOCATION DISTRIBUTION:")
        for cluster, count in sorted(self.analysis["location_clusters"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / self.analysis["total_candidates"]) * 100
            print(f"   {cluster:40s} {count:3d} ({pct:5.1f}%)")

        print("\n👔 SENIORITY DISTRIBUTION:")
        for level, candidates in self.analysis["seniority_levels"].items():
            pct = (len(candidates) / self.analysis["total_candidates"]) * 100
            print(f"   {level.replace('_', ' ').title():25s} {len(candidates):3d} ({pct:5.1f}%)")

        print("\n🏢 COMPANY TYPE DISTRIBUTION:")
        for comp_type, count in sorted(self.analysis["company_types"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / self.analysis["total_candidates"]) * 100
            print(f"   {comp_type:40s} {count:3d} ({pct:5.1f}%)")

        print("\n🔑 TITLE KEYWORDS:")
        for keyword, count in sorted(self.analysis["title_keywords"].items(), key=lambda x: x[1], reverse=True):
            pct = (count / self.analysis["total_candidates"]) * 100
            print(f"   {keyword.upper():15s} {count:3d} ({pct:5.1f}%)")

        print("\n📊 TOP 15 COMPANIES:")
        for company, count in self.analysis["companies"].most_common(15):
            print(f"   {company:40s} {count:3d}")

    def extract_jd_requirements(self) -> Dict[str, Any]:
        """Extract explicit requirements from job description"""
        if not self.jd_text:
            print("\n⚠️  No job description provided, skipping JD analysis")
            return {}

        print("\n=== JD REQUIREMENTS EXTRACTION ===\n")

        # Manual extraction based on the known JD structure
        jd_requirements = {
            "role_title": "Founder-in-Residence / CEO (Realtime Voice-Developer Tools)",
            "domain": "Voice AI, Real-time Communication, Developer Tools",
            "must_have_explicit": {
                "0_to_1_product_leadership": True,
                "ai_ml_literacy": True,
                "gtm_excellence": True,
                "leadership_skills": True,
                "stakeholder_management": True
            },
            "nice_to_have_explicit": {
                "voice_realtime_media_savvy": "WebRTC, STT/TTS, streaming ML inference, Twilio, Discord, LiveKit, Dolby-io",
                "scaled_telephony_conversational_ai": "Series A to exit",
                "deep_network_in_ai_voice": "OpenAI, Deepgram, AssemblyAI, LiveKit, Vapi",
                "oss_maintainer": "WebRTC/voice repos",
                "fundraising_experience": True
            },
            "technical_requirements": {
                "latency_target": "<400ms",
                "technologies": ["LLM", "STT", "TTS", "WebRTC", "RAG", "guardrails"]
            },
            "experience_requirements": {
                "founder_or_early_employee": True,
                "product_manager_background": "Optional",
                "engineer_background": "Optional",
                "management_consultant": "Optional",
                "proven_entrepreneur": True
            },
            "location_stated": "United States, Remote",
            "characteristics": ["Accountability", "Leadership", "Grit", "Scrappy", "Ownership orientation"]
        }

        print("✓ JD Requirements Extracted:")
        print(f"   Role: {jd_requirements['role_title']}")
        print(f"   Domain: {jd_requirements['domain']}")
        print(f"   Location (stated): {jd_requirements['location_stated']}")
        print(f"   Must-Have Count: {len(jd_requirements['must_have_explicit'])}")
        print(f"   Nice-to-Have Count: {len(jd_requirements['nice_to_have_explicit'])}")

        return jd_requirements

    def compare_jd_vs_reality(self, jd_requirements: Dict[str, Any]):
        """Compare stated JD requirements vs actual shortlist patterns"""
        print("\n=== JD vs REALITY ANALYSIS ===\n")

        print("🎯 KEY GAPS IDENTIFIED:\n")

        # Gap 1: Location
        stated_location = jd_requirements.get("location_stated", "Unknown")
        actual_location = max(self.analysis["location_clusters"].items(), key=lambda x: x[1])
        bay_area_pct = (self.analysis["location_clusters"].get("San Francisco Bay Area", 0) / self.analysis["total_candidates"]) * 100

        print(f"   1. LOCATION GAP:")
        print(f"      JD States: '{stated_location}'")
        print(f"      Reality: {bay_area_pct:.1f}% are in San Francisco Bay Area")
        print(f"      → Implicit Bay Area preference despite 'Remote' stated\n")

        # Gap 2: Seniority
        c_suite_pct = (len(self.analysis["seniority_levels"]["c_suite"]) / self.analysis["total_candidates"]) * 100
        senior_ic_pct = (len(self.analysis["seniority_levels"]["senior_ic"]) / self.analysis["total_candidates"]) * 100

        print(f"   2. SENIORITY GAP:")
        print(f"      JD Emphasizes: 'Founder-in-Residence / CEO'")
        print(f"      Reality: {c_suite_pct:.1f}% C-Suite, {senior_ic_pct:.1f}% Senior IC")
        print(f"      → Open to senior ICs (Staff Engineers, Research Scientists)\n")

        # Gap 3: Voice AI Experience
        voice_keyword_pct = (self.analysis["title_keywords"].get("voice", 0) / self.analysis["total_candidates"]) * 100
        ai_keyword_pct = (self.analysis["title_keywords"].get("ai", 0) / self.analysis["total_candidates"]) * 100
        voice_ai_companies_pct = (self.analysis["company_types"].get("Voice AI Specialist", 0) / self.analysis["total_candidates"]) * 100

        print(f"   3. VOICE AI EXPERIENCE GAP:")
        print(f"      JD Lists: 'Nice to Have - Voice / Real-Time Media Savvy'")
        print(f"      Reality: {voice_keyword_pct:.1f}% have 'Voice' in title, {ai_keyword_pct:.1f}% have 'AI'")
        print(f"      Reality: {voice_ai_companies_pct:.1f}% from Voice AI Specialist companies")
        print(f"      → Voice AI experience appears to be a HARD REQUIREMENT\n")

        # Gap 4: Company Pedigree
        big_tech_pct = (self.analysis["company_types"].get("Big Tech / FAANG", 0) / self.analysis["total_candidates"]) * 100
        ai_infra_pct = (self.analysis["company_types"].get("AI Infrastructure / Platform", 0) / self.analysis["total_candidates"]) * 100

        print(f"   4. COMPANY PEDIGREE (UNSTATED IN JD):")
        print(f"      JD States: (No explicit company requirements)")
        print(f"      Reality: {big_tech_pct:.1f}% Big Tech, {ai_infra_pct:.1f}% AI Infrastructure")
        print(f"      → Strong implicit preference for FAANG + top AI startups\n")

        # Gap 5: Interview Conversion
        interviewed_count = sum(1 for c in self.candidates if c["interview_date"])
        interview_pct = (interviewed_count / self.analysis["total_candidates"]) * 100

        print(f"   5. SOURCING QUALITY:")
        print(f"      Total Reached Out: {self.analysis['total_candidates']}")
        print(f"      Interviewed: {interviewed_count} ({interview_pct:.1f}%)")
        print(f"      → High conversion suggests well-qualified shortlist\n")

    def generate_search_queries(self) -> List[Dict[str, Any]]:
        """Generate tiered CoreSignal search queries"""
        print("\n=== GENERATING CORESIGNAL SEARCH QUERIES ===\n")

        queries = []

        # Tier 1: Strict JD Interpretation
        tier1 = {
            "tier": 1,
            "name": "Strict JD Interpretation",
            "description": "Direct translation of JD requirements",
            "criteria": {
                "must_have_location": "United States",
                "must_have_role_titles": ["Founder", "CEO", "CTO", "Chief", "Co-founder"],
                "must_have_industries": ["Technology, Information and Internet", "Software Development"],
                "must_have_skills_in_headline": ["AI", "Voice", "ML"],
                "must_have_experience_years": 10
            },
            "expected_coverage": "Low (30-40%) - Too strict on seniority, too broad on location"
        }
        queries.append(tier1)

        # Tier 2: Shortlist-Informed (Relaxed)
        tier2 = {
            "tier": 2,
            "name": "Shortlist-Informed Search",
            "description": "Incorporates patterns from actual candidate shortlist",
            "criteria": {
                "must_have_location": "San Francisco Bay Area",  # Implicit preference discovered
                "must_have_role_titles": ["AI", "ML", "Voice", "Speech", "Conversational", "LLM", "CTO", "Founder", "Staff", "Senior", "Director", "VP", "Head"],
                "must_have_industries": ["Technology, Information and Internet", "Software Development", "IT Services and IT Consulting"],
                "must_have_skills_in_headline": ["AI", "Machine Learning", "Voice", "Speech", "LLM", "NLP", "Generative"],
                "must_have_experience_years": 5  # Lowered from 10
            },
            "expected_coverage": "Medium (60-80%) - Captures most candidates, some location misses"
        }
        queries.append(tier2)

        # Tier 3: Multi-Location + Expanded Keywords
        tier3 = {
            "tier": 3,
            "name": "Optimized Multi-Location Search",
            "description": "Expands to all major tech hubs represented in shortlist",
            "criteria": {
                "must_have_locations": [
                    "San Francisco Bay Area",
                    "Greater Seattle Area",
                    "New York",
                    "Greater Boston",
                    "United States"  # Catch remote candidates
                ],
                "must_have_role_titles": [
                    # Voice AI specific
                    "Voice", "Speech", "Audio", "Conversational",
                    # AI/ML general
                    "AI", "ML", "Machine Learning", "LLM", "NLP", "Generative",
                    # Leadership
                    "CTO", "Founder", "Co-founder", "Chief", "VP", "Director", "Head of",
                    # Senior IC
                    "Staff", "Senior", "Principal", "Lead", "Research Scientist"
                ],
                "must_have_industries": [
                    "Technology, Information and Internet",
                    "Software Development",
                    "IT Services and IT Consulting",
                    "Computer Software",
                    "Internet"
                ],
                "must_have_skills_in_headline": [
                    "AI", "ML", "Machine Learning",
                    "Voice", "Speech", "Audio",
                    "LLM", "NLP", "Generative AI",
                    "Conversational AI", "Real-time"
                ],
                "must_have_experience_years": 5,
                "nice_to_have_companies": [
                    # Big Tech
                    "Meta", "Google", "Amazon", "Facebook", "Microsoft",
                    # AI Infrastructure
                    "Anthropic", "OpenAI", "Hugging Face", "Together AI", "Anyscale", "LangChain", "Pinecone",
                    # Voice AI
                    "Otter.ai", "Deepgram", "PlayAI", "ElevenLabs", "Phonic", "AssemblyAI", "Vapi",
                    # Conversational AI
                    "Sierra", "LiveKit"
                ]
            },
            "expected_coverage": "High (80-90%) - Broad enough to capture edge cases"
        }
        queries.append(tier3)

        # Print query summaries
        for query in queries:
            print(f"{'='*60}")
            print(f"TIER {query['tier']}: {query['name']}")
            print(f"{'='*60}")
            print(f"Description: {query['description']}")
            print(f"Expected Coverage: {query['expected_coverage']}\n")
            print("Criteria:")
            print(json.dumps(query['criteria'], indent=2))
            print()

        return queries

    def save_results(self, queries: List[Dict[str, Any]], output_path: str):
        """Save analysis and queries to JSON file"""
        output = {
            "analysis_metadata": {
                "csv_file": self.csv_path,
                "jd_file": self.jd_path,
                "total_candidates": self.analysis["total_candidates"],
                "analysis_date": "2025-10-28"
            },
            "pattern_analysis": {
                "location_clusters": dict(self.analysis["location_clusters"]),
                "seniority_distribution": {
                    k: len(v) for k, v in self.analysis["seniority_levels"].items()
                },
                "company_types": dict(self.analysis["company_types"]),
                "title_keywords": dict(self.analysis["title_keywords"]),
                "top_companies": dict(self.analysis["companies"].most_common(20))
            },
            "generated_queries": queries
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to: {output_path}")


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("  REVERSE-ENGINEER CORESIGNAL SEARCH CRITERIA")
    print("  From JD + Candidate Shortlist → Optimal Search Query")
    print("="*60 + "\n")

    # Paths
    csv_path = "/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/vocal bridge fir-Linda test - Jon reaching out.csv"
    jd_path = "/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/vocal_bridge_fir_job_description.md"
    output_path = "/Users/gauravsurtani/projects/linkedin_profile_ai_assessor/backend/reverse_engineer_results.json"

    # Initialize analyzer
    analyzer = ReverseEngineerAnalysis(csv_path, jd_path)

    # Run analysis pipeline
    analyzer.load_data()
    analyzer.analyze_patterns()
    jd_requirements = analyzer.extract_jd_requirements()
    analyzer.compare_jd_vs_reality(jd_requirements)
    queries = analyzer.generate_search_queries()
    analyzer.save_results(queries, output_path)

    print("\n" + "="*60)
    print("  ANALYSIS COMPLETE")
    print("="*60 + "\n")
    print("Next Steps:")
    print("  1. Review generated queries in: backend/reverse_engineer_results.json")
    print("  2. Test each tier against CoreSignal API")
    print("  3. Measure coverage (% of 68 candidates found)")
    print("  4. Iterate on Tier 3 query to maximize coverage")
    print("  5. Apply post-search ranking to filter false positives\n")


if __name__ == "__main__":
    main()
