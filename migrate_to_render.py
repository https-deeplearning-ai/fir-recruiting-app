#!/usr/bin/env python3
"""
Migration script to prepare for Render deployment
This script helps verify the configuration and provides deployment guidance
"""

import os
import sys

def check_environment():
    """Check current deployment environment"""
    is_render = os.getenv('RENDER') is not None
    is_heroku = os.getenv('DYNO') is not None
    
    print("🔍 Environment Detection:")
    if is_render:
        print("   ✅ Running on Render")
        return 'render'
    elif is_heroku:
        print("   ✅ Running on Heroku")
        return 'heroku'
    else:
        print("   ⚠️  Running locally")
        return 'local'

def check_configuration():
    """Check current configuration settings"""
    try:
        # Add backend directory to path
        import sys
        sys.path.append('backend')
        from config import MAX_CONCURRENT_CALLS, TIMEOUT_SECONDS, BATCH_SIZE, WORKERS
        print("🔧 Configuration:")
        print(f"   MAX_CONCURRENT_CALLS: {MAX_CONCURRENT_CALLS}")
        print(f"   TIMEOUT_SECONDS: {TIMEOUT_SECONDS}")
        print(f"   BATCH_SIZE: {BATCH_SIZE}")
        print(f"   WORKERS: {WORKERS}")
        return True
    except ImportError as e:
        print(f"   ❌ Configuration error: {e}")
        return False

def check_environment_variables():
    """Check required environment variables"""
    required_vars = [
        'ANTHROPIC_API_KEY',
        'CORESIGNAL_API_KEY', 
        'SUPABASE_URL',
        'SUPABASE_KEY'
    ]
    
    print("🔑 Environment Variables:")
    all_present = True
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing")
            all_present = False
    
    return all_present

def main():
    """Main migration check"""
    print("🚀 LinkedIn AI Assessor - Render Migration Check")
    print("=" * 50)
    
    # Check environment
    env = check_environment()
    print()
    
    # Check configuration
    config_ok = check_configuration()
    print()
    
    # Check environment variables
    env_vars_ok = check_environment_variables()
    print()
    
    # Summary
    print("📊 Summary:")
    if config_ok and env_vars_ok:
        print("   ✅ Ready for deployment!")
        if env == 'heroku':
            print("   📝 Next step: Deploy to Render using RENDER_DEPLOYMENT.md")
        elif env == 'render':
            print("   🎉 Successfully running on Render!")
        else:
            print("   🏠 Running locally - ready for Render deployment")
    else:
        print("   ❌ Issues found - please fix before deployment")
        sys.exit(1)

if __name__ == "__main__":
    main()
