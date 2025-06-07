"""
Simplified Slide Routes
Clean API endpoints for AI coaching with navigation guidance
"""

from flask import Blueprint, jsonify, request, render_template
import os
from typing import Dict, Any
import logging

from .slide_controller import get_slide_controller
from .voice_interaction import get_voice_interaction, process_voice_input, has_navigation_intent
from .lesson_coaching_manager import LessonCoachingManager
from .slide_content import get_slide_content

logger = logging.getLogger(__name__)

# Create blueprint
slide_routes = Blueprint('slides', __name__)

# Get global instances
slide_controller = get_slide_controller()
voice_interaction = get_voice_interaction()
slide_content = get_slide_content()

# Dictionary to store lesson coaching managers by lesson ID
lesson_managers = {}

def get_lesson_manager(lesson_id: str) -> LessonCoachingManager:
    """Get or create a LessonCoachingManager instance for a lesson"""
    if lesson_id not in lesson_managers:
        lesson_managers[lesson_id] = LessonCoachingManager(lesson_id)
    return lesson_managers[lesson_id]

@slide_routes.route('/slides')
def show_slides():
    """Render the slide presentation"""
    try:
        # Get current slide info
        nav_info = slide_controller.get_navigation_info()
        current_slide = nav_info['current_slide']
        
        # Set current lesson context
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')  # Default to ai-ux-design if not specified
        slide_content.set_current_lesson(lesson_id)
        
        # Get slide content and coaching context
        slide_content_data = slide_content.get_slide_content(current_slide)
        lesson_manager = get_lesson_manager(lesson_id)
        coaching_context = lesson_manager.get_status()
        
        return render_template('lesson.html', 
                             slide_info=nav_info,
                             slide_content=slide_content_data,
                             coaching_context=coaching_context,
                             lesson={'title': 'AI-Powered UX Design Workshop'},
                             lesson_id=lesson_id,
                             total_slides=nav_info['total_slides'])
    except Exception as e:
        logger.error(f"Error rendering slides: {e}")
        return jsonify({"error": "Failed to load slides"}), 500

@slide_routes.route('/api/slides/current')
def get_current_slide():
    """Get current slide content"""
    try:
        # Get current slide info
        nav_info = slide_controller.get_navigation_info()
        current_slide = nav_info['current_slide']
        
        # Set current lesson context
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')  # Default to ai-ux-design if not specified
        slide_content.set_current_lesson(lesson_id)
        
        # Get slide content
        slide_content_data = slide_content.get_slide_content(current_slide)
        
        return jsonify({
            "success": True,
            "slide": slide_content_data,
            "navigation": nav_info
        })
    except Exception as e:
        logger.error(f"Error getting current slide: {e}")
        return jsonify({"error": "Failed to get slide content"}), 500

@slide_routes.route('/api/slides/navigate', methods=['POST'])
def navigate_slides():
    """Handle slide navigation"""
    try:
        data = request.get_json()
        direction = data.get('direction', 'next')
        
        # Get current slide info
        nav_info = slide_controller.get_navigation_info()
        current_slide = nav_info['current_slide']
        
        # Set current lesson context
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')  # Default to ai-ux-design if not specified
        slide_content.set_current_lesson(lesson_id)
        
        # Navigate
        if direction == 'next':
            next_slide = current_slide + 1
        else:
            next_slide = current_slide - 1
            
        # Get slide content
        slide_content_data = slide_content.get_slide_content(next_slide)
        
        # Update navigation
        nav_info = slide_controller.get_navigation_info()
        
        return jsonify({
            "success": True,
            "slide": slide_content_data,
            "navigation": nav_info
        })
    except Exception as e:
        logger.error(f"Error navigating slides: {e}")
        return jsonify({"error": "Failed to navigate"}), 500

@slide_routes.route('/api/slides/search')
def search_slides():
    """Search slide content"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Search query required"}), 400
            
        # Set current lesson context
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')  # Default to ai-ux-design if not specified
        slide_content.set_current_lesson(lesson_id)
        
        # Search
        results = slide_content.search_content(query)
        
        return jsonify({
            "success": True,
            "query": query,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error searching slides: {e}")
        return jsonify({"error": "Failed to search"}), 500

@slide_routes.route('/api/slides/status')
def get_slide_status():
    """Get current slide status and coaching context"""
    try:
        nav_info = slide_controller.get_navigation_info()
        current_slide = nav_info['current_slide']
        slide_content_data = slide_content.get_slide_content(current_slide)
        
        # Get lesson context
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')
        lesson_manager = get_lesson_manager(lesson_id)
        coaching_context = lesson_manager.get_status()
        
        return jsonify({
            "success": True,
            "slide_info": nav_info,
            "slide_content": slide_content_data,
            "coaching_context": coaching_context
        })
    except Exception as e:
        logger.error(f"Error getting slide status: {e}")
        return jsonify({"error": "Failed to get slide status"}), 500

@slide_routes.route('/api/slides/manual_navigation', methods=['POST'])
def manual_navigation():
    """Handle manual navigation when user clicks UI buttons"""
    try:
        data = request.get_json()
        action = data.get('action')
        slide_number = data.get('slide_number')
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')
        
        # Execute the manual navigation
        if action == 'next':
            result = slide_controller.manual_next()
        elif action == 'previous':
            result = slide_controller.manual_previous()
        elif action == 'goto' and slide_number is not None:
            result = slide_controller.manual_goto(slide_number)
        else:
            return jsonify({"error": "Invalid navigation action"}), 400
        
        # Update coaching context and get response
        if result['success']:
            current_slide = result['current_slide']
            lesson_manager = get_lesson_manager(lesson_id)
            coaching_response = lesson_manager.process_user_input("User navigated to slide " + str(current_slide), current_slide)
            result['coaching_response'] = coaching_response['coaching_response']
            result['slide_content'] = slide_content.get_slide_content(current_slide)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in manual navigation: {e}")
        return jsonify({"error": "Manual navigation failed"}), 500

@slide_routes.route('/api/voice/process', methods=['POST'])
def process_voice():
    """Process voice input for coaching and navigation guidance"""
    try:
        data = request.get_json()
        voice_input = data.get('text', '')
        input_type = data.get('type', 'voice')
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')
        
        if not voice_input:
            return jsonify({"error": "No voice input provided"}), 400
        
        # Process through lesson manager
        lesson_manager = get_lesson_manager(lesson_id)
        result = lesson_manager.process_user_input(voice_input, slide_controller.get_navigation_info()['current_slide'], input_type)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        return jsonify({"error": "Failed to process voice input"}), 500

@slide_routes.route('/api/coaching/update_profile', methods=['POST'])
def update_user_profile():
    """Update user profile for personalization"""
    try:
        data = request.get_json()
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')
        
        if not data:
            return jsonify({"error": "No profile data provided"}), 400
        
        lesson_manager = get_lesson_manager(lesson_id)
        lesson_manager.update_user_profile(data)
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully"
        })
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return jsonify({"error": "Failed to update profile"}), 500

@slide_routes.route('/api/coaching/context')
def get_coaching_context_api():
    """Get current coaching context"""
    try:
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')
        lesson_manager = get_lesson_manager(lesson_id)
        context = lesson_manager.get_status()
        
        return jsonify({
            "success": True,
            "context": context
        })
    except Exception as e:
        logger.error(f"Error getting coaching context: {e}")
        return jsonify({"error": "Failed to get coaching context"}), 500

@slide_routes.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset the current session"""
    try:
        lesson_id = request.args.get('lesson_id', 'ai-ux-design')
        if lesson_id in lesson_managers:
            lesson_managers[lesson_id].clear_history()
        
        return jsonify({
            "success": True,
            "message": "Session reset successfully"
        })
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        return jsonify({"error": "Failed to reset session"}), 500

@slide_routes.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.1.0"
    })

def register_routes(app):
    """Register slide routes with Flask app"""
    app.register_blueprint(slide_routes)

def get_blueprint():
    """Get the slide routes blueprint"""
    return slide_routes

def init_slide_system():
    """Initialize the slide system"""
    return True
