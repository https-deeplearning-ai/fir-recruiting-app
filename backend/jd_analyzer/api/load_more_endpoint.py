"""
Load More Candidates API Endpoint with Company Batching

This module provides endpoints for progressive loading with company batching
using SearchSessionManager and Supabase persistence.
"""

from flask import Blueprint, request, jsonify
import os
import sys
import time
import json
import asyncio
from typing import Dict, Any
from pathlib import Path

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.search_session import SearchSessionManager
from jd_analyzer.api.domain_search import stage2_preview_search

# Create blueprint
bp = Blueprint('domain_load_more', __name__, url_prefix='/api/jd')


@bp.route('/load-more-previews', methods=['POST'])
def load_more_previews():
    """
    Load additional preview candidates using company batching.

    This endpoint uses SearchSessionManager to load the next batch of companies
    and fetch candidates progressively, maintaining search quality.

    Request JSON:
    {
        "session_id": "search_abc123",
        "count": 100,  // How many more to load (20/40/100)
        "mode": "company_batch"  // or "seniority_variation" (future)
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id')
        count = data.get('count', 100)
        mode = data.get('mode', 'company_batch')

        if not session_id:
            return jsonify({
                "success": False,
                "error": "session_id is required"
            }), 400

        print(f"\n📥 Load More Request:")
        print(f"   Session: {session_id}")
        print(f"   Mode: {mode}")
        print(f"   Requesting: {count} more candidates")

        # Initialize session manager
        session_manager = SearchSessionManager()

        # Get session data
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({
                "success": False,
                "error": "Session not found or expired"
            }), 404

        # Check if session is active
        if not session.get('is_active'):
            return jsonify({
                "success": False,
                "error": "Session has been cleared"
            }), 410

        # Get original query from session
        search_query = json.loads(session['search_query'])
        jd_requirements = search_query.get('jd_requirements', {})
        endpoint = search_query.get('endpoint', 'employee_clean')
        max_previews = search_query.get('max_previews', 100)  # Increased from 20 to 100 for experience-based search

        # Initialize results
        all_new_profiles = []
        batches_processed = 0
        max_batches = count // 100  # Process enough batches for requested count (100 per batch)

        # Process batches until we have enough candidates or run out
        for _ in range(max_batches):
            # Get next company batch
            next_batch = session_manager.get_next_batch(session_id)
            if not next_batch:
                print(f"   ℹ️  No more company batches available")
                break

            print(f"\n   📦 Processing batch: {next_batch}")

            # Rate limit protection
            if batches_processed > 0:
                time.sleep(2)

            # Create async event loop for stage2
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run stage2 with the next batch (don't create new session)
                result = loop.run_until_complete(
                    stage2_preview_search(
                        companies=[{'name': c} for c in next_batch],
                        jd_requirements=jd_requirements,
                        endpoint=endpoint,
                        max_previews=max_previews,
                        create_session=False,  # Don't create new session
                        session_id=session_id   # Use existing session
                    )
                )

                if result.get('previews'):
                    all_new_profiles.extend(result['previews'])
                    batches_processed += 1
                    print(f"   ✅ Got {len(result['previews'])} candidates from batch")

            finally:
                loop.close()

            # Check if we have enough
            if len(all_new_profiles) >= count:
                break

        # Get updated session stats
        stats = session_manager.get_session_stats(session_id)

        # Prepare response
        response_data = {
            "success": True,
            "new_profiles": all_new_profiles[:count],  # Limit to requested count
            "total_discovered": stats.get('discovered_ids', 0),
            "batch_index": stats.get('batches_completed', 0),
            "remaining_batches": stats.get('total_batches', 0) - stats.get('batches_completed', 0),
            "session_stats": {
                "total_discovered": stats.get('discovered_ids', 0),
                "batches_completed": stats.get('batches_completed', 0),
                "total_batches": stats.get('total_batches', 0),
                "profiles_fetched": stats.get('profiles_fetched', 0)
            }
        }

        print(f"\n   📊 Load More Complete:")
        print(f"      New profiles: {len(all_new_profiles)}")
        print(f"      Total discovered: {stats.get('discovered_ids', 0)}")
        print(f"      Batches processed: {batches_processed}")

        return jsonify(response_data)

    except Exception as e:
        import traceback
        print(f"❌ Load more endpoint error: {e}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/list-sessions', methods=['GET'])
def list_sessions():
    """
    List all active search sessions.
    """
    try:
        session_manager = SearchSessionManager()
        sessions = session_manager.list_active_sessions(limit=50)

        return jsonify({
            "success": True,
            "sessions": sessions
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/clear-session', methods=['POST'])
def clear_session():
    """
    Clear a specific search session.
    """
    try:
        data = request.json
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({
                "success": False,
                "error": "session_id is required"
            }), 400

        session_manager = SearchSessionManager()
        success = session_manager.clear_session(session_id)

        if success:
            return jsonify({
                "success": True,
                "message": f"Session {session_id} cleared"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to clear session"
            }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/clear-all-sessions', methods=['POST'])
def clear_all_sessions():
    """
    Clear all active search sessions (admin function).
    """
    try:
        session_manager = SearchSessionManager()
        cleared_count = session_manager.clear_all_sessions()

        return jsonify({
            "success": True,
            "message": f"Cleared {cleared_count} sessions"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/session-stats', methods=['GET'])
def get_session_stats():
    """
    Get detailed statistics for a search session.
    """
    try:
        session_id = request.args.get('session_id')

        if not session_id:
            return jsonify({
                "success": False,
                "error": "session_id is required"
            }), 400

        session_manager = SearchSessionManager()
        stats = session_manager.get_session_stats(session_id)

        if not stats:
            return jsonify({
                "success": False,
                "error": "Session not found"
            }), 404

        return jsonify({
            "success": True,
            "stats": stats
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Export blueprint
__all__ = ['bp']