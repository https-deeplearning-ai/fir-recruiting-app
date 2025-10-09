import os
import json
import requests
import time
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
CORESIGNAL_API_KEY = "zGZEUYUw2Koty9kxPidzCHTce5Wl2vYL"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Initialize Anthropic client
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

# Load valid input values from JSON file
# This file contains all valid values for management_level, department, company_industry, etc.
# The AI will reference these exact values for every search to ensure accurate filtering
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
input_values_path = os.path.join(script_dir, 'input_values.json')
with open(input_values_path, 'r') as f:
    VALID_INPUT_VALUES = json.load(f)

# Test with both complex and simple prompts
complex_prompt = "We are seeking a visionary and entrepreneurial leader based in the United States to serve as the future CEO of a real-time voice AI startup. The ideal candidate brings repeat startup leadership experience (0→1 track record in B2B SaaS or infrastructure), strong AI/ML literacy, and a proven ability to drive go-to-market success, fundraising, and stakeholder engagement. This individual should be equally comfortable shaping product and technology strategy, recruiting top-tier teams, and inspiring investors, partners, and customers with a compelling narrative. Experience with real-time voice, developer-first products, or the AI voice ecosystem is a plus. Above all, we value leaders with grit, accountability, scrappiness, and a deep sense of ownership—someone who can refine the vision, execute under pressure, and build a category-defining company."

# Test various types of prompts
simple_ai_prompt = "Find me a technical leader based in the United States who works in the technology industry and has AI or machine learning experience."
sales_prompt = "Find me a sales director in healthcare based in New York"
founder_prompt = "Find me a founder of a software company with 10+ years experience"
generic_prompt = "Find me a product manager who worked in tech"

# Use the simple prompt for testing
user_prompt = simple_ai_prompt

def process_user_prompt_with_anthropic(user_prompt: str) -> Dict[str, Any]:
    """
    Process the user prompt using Anthropic API to generate intelligent search criteria.
    Makes inferences from imperfect prompts and balances accuracy with search breadth.
    """
    # Get tech-related industries from the valid values
    tech_industries = [ind for ind in VALID_INPUT_VALUES['company_industry'] if any(keyword in ind for keyword in [
        'Technology', 'Software', 'IT ', 'Computer', 'Internet', 'Data', 'Mobile', 'Desktop', 'Embedded', 'Blockchain'
    ])]
    
    # Build the system prompt with ALL valid values from input_values.json
    management_levels_str = json.dumps(VALID_INPUT_VALUES['management_level'], indent=2)
    departments_str = json.dumps(VALID_INPUT_VALUES['department'], indent=2)
    tech_industries_str = json.dumps(tech_industries, indent=2)
    all_industries_str = json.dumps(VALID_INPUT_VALUES['company_industry'], indent=2)
    total_industries = len(VALID_INPUT_VALUES['company_industry'])
    
    system_prompt = f"""You are an expert at extracting MINIMUM REQUIREMENTS from user prompts for LinkedIn profile searches and mapping them to valid Coresignal database values.

CRITICAL: 
1. Extract ONLY the absolute minimum requirements that MUST be met
2. You MUST use ONLY exact values from the provided lists - DO NOT make up or modify values
3. If user mentions an industry, find the closest matching value from the exact list
4. These will be used as hard filters - candidates must meet ALL requirements

===== VALID FIELD VALUES (USE ONLY THESE) =====

**management_level:** (Choose from ONLY these {len(VALID_INPUT_VALUES['management_level'])} exact values)
{management_levels_str}

**department:** (Choose from ONLY these {len(VALID_INPUT_VALUES['department'])} exact values)
{departments_str}

**company_industry:** (Choose from ONLY these {total_industries} exact values)

TECHNOLOGY-RELATED INDUSTRIES (most common for tech searches):
{tech_industries_str}

ALL AVAILABLE INDUSTRIES (full list - search this for non-tech):
{all_industries_str}

IMPORTANT: When user mentions an industry, you MUST find and use the EXACT matching value from the lists above.

Return a JSON object with ONLY minimum requirements:
{{
    "must_have_location": "United States",  // Required location (country/city) or null if not specified
    "must_have_industries": ["Technology, Information and Internet", "Software Development"],  // Required industries - use exact schema values (at least one must match)
    "must_have_role_titles": ["CTO", "Director", "VP", "Head", "Lead", "Chief"],  // Required words in job title (at least one must match)
    "must_have_management_levels": ["C-Level", "Director", "VP"],  // Required leadership levels (at least one must match)
    "must_have_departments": null,  // ONLY include if user explicitly mentions "engineering department" or "product team" - otherwise set to null
    "must_have_skills_in_headline": ["AI", "ML", "Machine Learning"],  // Required keywords in headline/skills (at least one must match)
    "must_have_experience_years": 5,  // Minimum years of experience or null
    "explanation": "Technical leader = CTO/Director/VP/Head, Tech industry = Technology/Software companies, AI/ML = must mention in headline"
}}

EXTRACTION GUIDELINES:

1. **Location**: 
   - Extract ONLY if explicitly mentioned (e.g., "United States", "San Francisco", "New York", "Europe")
   - Set to null if "remote", "anywhere", or location not mentioned
   - Use common names: "United States" not "USA"

2. **Industry**: 
   - Extract ONLY if explicitly mentioned (e.g., "tech industry", "software company", "healthcare", "finance")
   - Map to exact values from the list above
   - Do NOT infer industry from role (e.g., "CTO" doesn't automatically mean tech industry)
   - For "tech/technology" → use ["Technology, Information and Internet", "Software Development", "IT Services and IT Consulting", "Computer Software"]
   - For "software" → use ["Software Development", "Computer Software"]
   - For "AI" → use ["Data Infrastructure and Analytics", "Software Development"]
   - For "healthcare" → use ["Hospitals and Health Care", "Medical Practices"]

3. **Role/Title Keywords**: 
   - Extract keywords that should appear in job_title field
   - Examples:
     * "CEO" or "chief executive" → ["CEO", "Chief Executive"]
     * "CTO" or "technical leader" → ["CTO", "Chief Technology"]
     * "founder" → ["Founder", "Co-Founder"]
     * "director" → ["Director"]
     * "VP" or "vice president" → ["VP", "Vice President"]
     * "head of" → ["Head"]
     * "manager" → ["Manager"]
     * "engineer" → ["Engineer", "Engineering"]
     * "sales leader" → ["Sales"]
   - Be specific - don't add too many generic terms

4. **Management Level**: 
   - Map to EXACT values from the list
   - Only include if role implies leadership
   - Examples:
     * "C-level", "executive", "CEO", "CTO" → ["C-Level"]
     * "director" → ["Director"]
     * "VP", "vice president" → ["VP"]
     * "senior leader" → ["Director", "VP", "Head", "Senior"]
     * "manager" → ["Manager"]
     * "founder" → ["Founder"]
   - If role titles are already specified, management_levels can be more relaxed

5. **Skills in Headline**: 
   - Extract specific technical or professional skills that MUST be mentioned
   - Only include skills explicitly mentioned in the prompt
   - Examples:
     * "AI/ML experience" → ["AI", "ML", "Machine Learning"]
     * "Python developer" → ["Python"]
     * "data science" → ["Data Science", "Data"]
     * "leadership skills" → ["Leadership"]
     * "sales experience" → ["Sales"]
   - Keep the list short (3-5 key skills max)

6. **Department**: 
   - ONLY include if explicitly mentioned with department name
   - Map to EXACT values from the list
   - Examples:
     * "engineering team" or "engineering department" → ["Engineering and Technical"]
     * "product team" → ["Product"]
     * "sales team" → ["Sales"]
   - If not explicitly mentioned, set to null (most profiles don't have this field)

7. **Experience Years**:
   - Extract ONLY if explicitly mentioned
   - Examples: "5+ years" → 5, "10 years experience" → 10
   - Set to null if not mentioned

IMPORTANT PRINCIPLES:
- Be conservative - only extract what's explicitly stated
- Use exact values from the provided lists
- Don't over-infer - if unsure, leave as null or use broader terms
- Balance specificity (to get quality) with flexibility (to get results)
- The goal is to find candidates who meet ALL requirements, so each requirement should be essential

Focus on extracting clear, essential minimum requirements."""

    try:
        response = anthropic.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract the JSON response
        response_text = response.content[0].text
        
        # Try to parse the JSON response
        try:
            # Look for JSON in the response (it might be wrapped in markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from Anthropic response: {response_text}")
            return {}
            
    except Exception as e:
        print(f"Error calling Anthropic API: {e}")
        return {}

def build_elasticsearch_dsl_query(criteria: Dict[str, Any], limit: int = 1) -> Dict[str, Any]:
    """
    Build Elasticsearch DSL query from the extracted criteria.
    """
    must_conditions = []
    should_conditions = []
    
    # Job titles (must match)
    if criteria.get("job_titles"):
        job_title_conditions = []
        for title in criteria["job_titles"]:
            job_title_conditions.append({
                "wildcard": {
                    "job_title": f"*{title.lower()}*"
                }
            })
            job_title_conditions.append({
                "wildcard": {
                    "experience.title": f"*{title.lower()}*"
                }
            })
        should_conditions.extend(job_title_conditions)
    
    # Experience levels (should match)
    if criteria.get("experience_levels"):
        exp_level_conditions = []
        for level in criteria["experience_levels"]:
            exp_level_conditions.append({
                "wildcard": {
                    "management_level": f"*{level.lower()}*"
                }
            })
        should_conditions.extend(exp_level_conditions)
    
    # Skills (should match in skills array or job descriptions)
    if criteria.get("skills"):
        for skill in criteria["skills"]:
            should_conditions.append({
                "term": {
                    "skills": skill.lower()
                }
            })
            should_conditions.append({
                "wildcard": {
                    "job_description": f"*{skill.lower()}*"
                }
            })
            should_conditions.append({
                "wildcard": {
                    "headline": f"*{skill.lower()}*"
                }
            })
    
    # Industries (should match)
    if criteria.get("industries"):
        for industry in criteria["industries"]:
            should_conditions.append({
                "wildcard": {
                    "company_industry": f"*{industry.lower()}*"
                }
            })
    
    # Education (should match)
    if criteria.get("education"):
        for edu in criteria["education"]:
            should_conditions.append({
                "wildcard": {
                    "education.major": f"*{edu.lower()}*"
                }
            })
    
    # Location (must match)
    if criteria.get("locations"):
        location_conditions = []
        for location in criteria["locations"]:
            location_conditions.append({
                "wildcard": {
                    "location_country": f"*{location.lower()}*"
                }
            })
            location_conditions.append({
                "wildcard": {
                    "location_raw_address": f"*{location.lower()}*"
                }
            })
        should_conditions.extend(location_conditions)
    
    # Management levels (should match)
    if criteria.get("management_levels"):
        for mgmt_level in criteria["management_levels"]:
            should_conditions.append({
                "wildcard": {
                    "management_level": f"*{mgmt_level.lower()}*"
                }
            })
    
    # Company types (should match)
    if criteria.get("company_types"):
        for company_type in criteria["company_types"]:
            should_conditions.append({
                "wildcard": {
                    "company_type": f"*{company_type.lower()}*"
                }
            })
    
    # Specialized experience (should match in descriptions)
    if criteria.get("specialized_experience"):
        for spec_exp in criteria["specialized_experience"]:
            should_conditions.append({
                "wildcard": {
                    "job_description": f"*{spec_exp.lower()}*"
                }
            })
            should_conditions.append({
                "wildcard": {
                    "experience.description": f"*{spec_exp.lower()}*"
                }
            })
    
    # Company sizes (should match)
    if criteria.get("company_sizes"):
        size_conditions = []
        for size in criteria["company_sizes"]:
            if size == "1-10":
                size_conditions.append({
                    "range": {
                        "company_size_employees_count": {
                            "gte": 1,
                            "lte": 10
                        }
                    }
                })
            elif size == "11-50":
                size_conditions.append({
                    "range": {
                        "company_size_employees_count": {
                            "gte": 11,
                            "lte": 50
                        }
                    }
                })
            elif size == "51-200":
                size_conditions.append({
                    "range": {
                        "company_size_employees_count": {
                            "gte": 51,
                            "lte": 200
                        }
                    }
                })
        should_conditions.extend(size_conditions)
    
    # Years of experience (should match)
    if criteria.get("years_experience_min") or criteria.get("years_experience_max"):
        exp_range = {}
        if criteria.get("years_experience_min"):
            exp_range["gte"] = criteria["years_experience_min"] * 12  # Convert to months
        if criteria.get("years_experience_max"):
            exp_range["lte"] = criteria["years_experience_max"] * 12  # Convert to months
        
        if exp_range:
            should_conditions.append({
                "range": {
                    "total_experience_duration_months": exp_range
                }
            })
    
    # Keywords (should match in various fields)
    if criteria.get("keywords"):
        for keyword in criteria["keywords"]:
            should_conditions.append({
                "wildcard": {
                    "headline": f"*{keyword.lower()}*"
                }
            })
            should_conditions.append({
                "wildcard": {
                    "job_description": f"*{keyword.lower()}*"
                }
            })
            should_conditions.append({
                "wildcard": {
                    "description": f"*{keyword.lower()}*"
                }
            })
    
    # Build the final query
    query = {
        "size": limit,
        "query": {
            "bool": {
                "must": [
                    {
                        "term": {
                            "is_working": 1  # Only active profiles
                        }
                    }
                ]
            }
        }
    }
    
    # Add should conditions if any exist
    if should_conditions:
        query["query"]["bool"]["should"] = should_conditions
        query["query"]["bool"]["minimum_should_match"] = 1
    
    # Add sorting by relevance and experience
    query["sort"] = [
        {
            "_score": {
                "order": "desc"
            }
        },
        {
            "total_experience_duration_months": {
                "order": "desc"
            }
        }
    ]
    
    return query

def create_coresignal_filters(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create comprehensive Coresignal filters from extracted criteria.
    """
    filters = {}
    
    # Job titles - prioritize CEO/Founder titles
    if criteria.get("job_titles"):
        # Look for the most relevant titles first
        priority_titles = ["CEO", "Chief Executive Officer", "Founder", "Co-Founder", "President"]
        selected_title = None
        
        for title in priority_titles:
            if title in criteria["job_titles"]:
                selected_title = title
                break
        
        if not selected_title:
            selected_title = criteria["job_titles"][0]
        
        filters["job_title"] = selected_title
    
    # Experience level - prefer Executive/C-Level
    if criteria.get("management_levels"):
        priority_levels = ["C-Level", "Executive", "Founder"]
        selected_level = None
        
        for level in priority_levels:
            if level in criteria["management_levels"]:
                selected_level = level
                break
        
        if not selected_level:
            selected_level = criteria["management_levels"][0]
        
        filters["management_level"] = selected_level
    
    # Industry - prefer Technology/AI related
    if criteria.get("industries"):
        priority_industries = ["Technology", "Artificial Intelligence", "Software Development", "SaaS"]
        selected_industry = None
        
        for industry in priority_industries:
            if industry in criteria["industries"]:
                selected_industry = industry
                break
        
        if not selected_industry:
            selected_industry = criteria["industries"][0]
        
        filters["industry"] = selected_industry
    
    # Location (if specified)
    if criteria.get("locations"):
        filters["location"] = criteria["locations"][0]
    
    # Company type - prefer Startup
    if criteria.get("company_types"):
        priority_types = ["Startup", "B2B", "SaaS"]
        selected_type = None
        
        for company_type in priority_types:
            if company_type in criteria["company_types"]:
                selected_type = company_type
                break
        
        if not selected_type:
            selected_type = criteria["company_types"][0]
        
        filters["company_type"] = selected_type
    
    # Company size - prefer smaller startups
    if criteria.get("company_sizes"):
        priority_sizes = ["1-10", "11-50", "51-200"]
        selected_size = None
        
        for size in priority_sizes:
            if size in criteria["company_sizes"]:
                selected_size = size
                break
        
        if not selected_size:
            selected_size = criteria["company_sizes"][0]
        
        filters["company_size"] = selected_size
    
    # Years of experience
    if criteria.get("years_experience_min"):
        filters["years_experience_min"] = criteria["years_experience_min"]
    
    return filters

def build_intelligent_elasticsearch_query(criteria: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build Elasticsearch DSL query with ALL criteria as MUST conditions.
    Every candidate must meet ALL requirements.
    """
    must_conditions = []
    
    # Always include working status
    must_conditions.append({
        "term": {
            "is_working": 1
        }
    })
    
    # MUST: Location (if specified)
    if criteria.get("must_have_location"):
        location = criteria["must_have_location"]
        
        # Create location condition (at least one must match)
        location_conditions = []
        
        if location.lower() in ["united states", "us", "usa", "america"]:
            location_conditions.append({"term": {"location_country": "United States"}})
            location_conditions.append({"term": {"location_country": "US"}})
            location_conditions.append({"term": {"location_country": "USA"}})
        else:
            # For other locations, use wildcard
            location_conditions.append({
                "wildcard": {
                    "location_raw_address": f"*{location.lower()}*"
                }
            })
            location_conditions.append({
                "wildcard": {
                    "location_country": f"*{location.lower()}*"
                }
            })
        
        if location_conditions:
            must_conditions.append({
                "bool": {
                    "should": location_conditions,
                    "minimum_should_match": 1
                }
            })
    
    # MUST: Industry (at least one must match)
    # Industry is in the nested experience field, use the exact subfield for keyword matching
    if criteria.get("must_have_industries"):
        industry_conditions = []
        for industry in criteria["must_have_industries"]:
            # Use nested query with exact field for case-sensitive keyword matching
            industry_conditions.append({
                "nested": {
                    "path": "experience",
                    "query": {
                        "term": {
                            "experience.company_industry.exact": industry
                        }
                    }
                }
            })
        
        if industry_conditions:
            must_conditions.append({
                "bool": {
                    "should": industry_conditions,
                    "minimum_should_match": 1
                }
            })
    
    # MUST: Role/Title (at least one keyword must appear in job title)
    if criteria.get("must_have_role_titles"):
        role_conditions = []
        for role in criteria["must_have_role_titles"]:
            role_conditions.append({
                "wildcard": {
                    "job_title": f"*{role.lower()}*"
                }
            })
        
        if role_conditions:
            must_conditions.append({
                "bool": {
                    "should": role_conditions,
                    "minimum_should_match": 1
                }
            })
    
    # Management Level is optional - if role title is already specified, this is redundant
    # Only add if no role titles are specified
    if criteria.get("must_have_management_levels") and not criteria.get("must_have_role_titles"):
        mgmt_conditions = []
        for level in criteria["must_have_management_levels"]:
            mgmt_conditions.append({
                "term": {
                    "management_level": level
                }
            })
        
        if mgmt_conditions:
            must_conditions.append({
                "bool": {
                    "should": mgmt_conditions,
                    "minimum_should_match": 1
                }
            })
    
    # MUST: Department (at least one must match) - if specified
    if criteria.get("must_have_departments"):
        dept_conditions = []
        for dept in criteria["must_have_departments"]:
            dept_conditions.append({
                "term": {
                    "department": dept
                }
            })
        
        if dept_conditions:
            must_conditions.append({
                "bool": {
                    "should": dept_conditions,
                    "minimum_should_match": 1
                }
            })
    
    # MUST: Skills in headline/skills (at least one must match)
    # Simplified to avoid 503 errors - just check headline and skills field
    if criteria.get("must_have_skills_in_headline"):
        skill_conditions = []
        for skill in criteria["must_have_skills_in_headline"][:3]:  # Limit to top 3 skills
            # Search in headline
            skill_conditions.append({
                "wildcard": {
                    "headline": f"*{skill.lower()}*"
                }
            })
            # Search in skills field  
            skill_conditions.append({
                "term": {
                    "skills": skill
                }
            })
        
        if skill_conditions:
            must_conditions.append({
                "bool": {
                    "should": skill_conditions,
                    "minimum_should_match": 1
                }
            })
    
    # MUST: Minimum years of experience (if specified)
    if criteria.get("must_have_experience_years"):
        must_conditions.append({
            "range": {
                "total_experience_duration_months": {
                    "gte": criteria["must_have_experience_years"] * 12
                }
            }
        })
    
    # Build the final query - ALL conditions are MUST
    query = {
        "query": {
            "bool": {
                "must": must_conditions
            }
        },
        "sort": ["_score"]
    }
    
    return query

def search_coresignal_profiles(criteria: Dict[str, Any], limit: int = 1) -> Dict[str, Any]:
    """
    Search for profiles using Coresignal Clean Employee API with comprehensive Elasticsearch DSL.
    """
    headers = {
        "accept": "application/json",
        "apikey": CORESIGNAL_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Build intelligent Elasticsearch DSL query from AI-processed criteria
    query = build_intelligent_elasticsearch_query(criteria)
    
    try:
        print("Submitting search request to Coresignal Search Preview API...")
        response = requests.post(
            "https://api.coresignal.com/cdapi/v2/employee_clean/search/es_dsl/preview",
            json=query,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Search request successful!")
            data = response.json()
            
            # Handle response format
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict) and 'data' in data:
                results = data['data']
            else:
                results = [data] if data else []
            
            return {
                "success": True,
                "results": results,
                "total_found": len(results),
                "query": query
            }
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return {"error": f"API error: {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error submitting request: {e}")
        return {"error": str(e)}

def search_profiles(user_prompt: str, limit: int = 1) -> Dict[str, Any]:
    """
    Main function to search for profiles based on user prompt.
    
    Args:
        user_prompt: The job description or candidate requirements
        limit: Number of profiles to return (default: 1)
    
    Returns:
        Dictionary containing search results or error information
    """
    print(f"🔍 Searching for {limit} profile(s) matching: {user_prompt[:100]}...")
    
    # Step 1: Process user prompt with Anthropic
    print("🤖 Processing prompt with Anthropic...")
    criteria = process_user_prompt_with_anthropic(user_prompt)
    
    if not criteria:
        return {"error": "Failed to extract criteria from user prompt"}
    
    print(f"✅ Extracted criteria: {json.dumps(criteria, indent=2)}")
    
    # Step 2: Build intelligent Elasticsearch DSL query
    print("🔧 Building intelligent Elasticsearch DSL query...")
    query = build_intelligent_elasticsearch_query(criteria)
    
    print(f"📋 Generated query: {json.dumps(query, indent=2)}")
    
    # Step 3: Search Coresignal API
    print("🌐 Searching Coresignal API...")
    results = search_coresignal_profiles(criteria, limit)
    
    return results

def main():
    """
    Main function to run the search.
    """
    # Check if Anthropic API key is available
    if not ANTHROPIC_API_KEY:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key: export ANTHROPIC_API_KEY='your_key_here'")
        return
    
    # Run the search
    results = search_profiles(user_prompt, limit=1)
    
    if "error" in results:
        print(f"❌ Search failed: {results['error']}")
        return
    
    if results.get("success"):
        print(f"\n🎉 Search completed successfully!")
        print(f"📊 Found {results['total_found']} profile(s)")
        
        # Display results
        for i, profile in enumerate(results["results"], 1):
            print(f"\n--- Profile {i} ---")
            print(f"Name: {profile.get('full_name', 'N/A')}")
            print(f"Title: {profile.get('job_title', 'N/A')}")
            print(f"Company: {profile.get('company_name', 'N/A')}")
            print(f"Location: {profile.get('location_raw_address', 'N/A')}")
            headline = profile.get('headline') or 'N/A'
            print(f"Headline: {headline[:100]}...")
            print(f"LinkedIn: {profile.get('websites_linkedin', 'N/A')}")
            
            # Save results to file
            output_file = f"search_results_{int(time.time())}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {output_file}")
    else:
        print(f"❌ Search failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()