import os

# Render-optimized configuration
# This file allows easy switching between Heroku and Render configurations

def get_config():
    """Get configuration based on deployment environment"""
    
    # Check if we're on Render (has RENDER environment variable)
    is_render = os.getenv('RENDER') is not None
    
    if is_render:
        # Render configuration - no timeout limits
        return {
            'MAX_CONCURRENT_CALLS': 50,  # Higher concurrency on Render
            'TIMEOUT_SECONDS': 60,       # Longer timeout for large batches
            'BATCH_SIZE': 100,           # Larger batch size
            'WORKERS': 2                 # Multiple workers for better performance
        }
    else:
        # Heroku configuration - conservative settings
        return {
            'MAX_CONCURRENT_CALLS': 15,  # Conservative for Heroku timeout
            'TIMEOUT_SECONDS': 25,       # Safety margin for Heroku 30s limit
            'BATCH_SIZE': 50,            # Smaller batch size
            'WORKERS': 1                 # Single worker
        }

# Export current configuration
config = get_config()
MAX_CONCURRENT_CALLS = config['MAX_CONCURRENT_CALLS']
TIMEOUT_SECONDS = config['TIMEOUT_SECONDS']
BATCH_SIZE = config['BATCH_SIZE']
WORKERS = config['WORKERS']

# Global list of companies to exclude from company research
# These are DLAI's own companies and should not be identified as competitors
EXCLUDED_COMPANIES = [
    "DLAI",
    "Deep Learning.AI",
    "AI Fund"
]

def is_excluded_company(company_name: str) -> bool:
    """
    Check if a company name matches any excluded company (exact match, case-insensitive).

    Args:
        company_name: Company name to check

    Returns:
        True if the company should be excluded, False otherwise
    """
    if not company_name:
        return False

    company_name_lower = company_name.strip().lower()
    return any(excluded.lower() == company_name_lower for excluded in EXCLUDED_COMPANIES)
