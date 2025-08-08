#!/usr/bin/env python3
"""
CLI Runner for Form-Filling Agent

This script provides a command-line interface to run the LangGraph form-filling agent.
Users can start the form-filling process with a simple command: python run_agent.py
"""

import sys
import argparse
from typing import Dict, Any
from agent import app


def create_session_config(thread_id: str = None) -> Dict[str, Any]:
    """Create a configuration for the agent session"""
    if thread_id is None:
        import uuid
        thread_id = f"form_session_{uuid.uuid4().hex[:8]}"
    
    return {"configurable": {"thread_id": thread_id}}


def initialize_state() -> Dict[str, Any]:
    """Initialize the form state for a new session"""
    return {
        "messages": [],
        "current_section": "",
        "completed_sections": [],
        "form_complete": False,
        "first_name": None,
        "last_name": None,
        "date_of_birth": None,
        "email": None,
        "phone": None,
        "address": None,
        "preferred_contact_method": None,
        "newsletter_subscription": None,
        "interests": None
    }


def print_welcome_banner():
    """Display a welcome banner for the CLI application"""
    print("\n" + "="*60)
    print("  🎯 CLI FORM-FILLING AGENT")
    print("  Powered by LangGraph")
    print("="*60)
    print("\nWelcome! This agent will help you fill out a form step by step.")
    print("You can press Ctrl+C at any time to exit.")
    print("\nLet's get started!\n")


def print_goodbye_message():
    """Display a goodbye message when the session ends"""
    print("\n" + "="*60)
    print("  👋 Thank you for using the Form-Filling Agent!")
    print("="*60)


def run_form_agent(thread_id: str = None, verbose: bool = False) -> bool:
    """
    Run the form-filling agent
    
    Args:
        thread_id: Optional thread ID for session management
        verbose: Whether to show verbose output
        
    Returns:
        bool: True if form was completed successfully, False otherwise
    """
    try:
        # Create session configuration
        config = create_session_config(thread_id)
        
        if verbose:
            print(f"Starting session with thread ID: {config['configurable']['thread_id']}")
        
        # Initialize state
        initial_state = initialize_state()
        
        # Run the agent
        result = app.invoke(initial_state, config)
        
        # Check if form was completed
        if result.get("form_complete"):
            print("\n🎉 Form completed successfully!")
            if verbose:
                print(f"Session ID: {config['configurable']['thread_id']}")
            return True
        else:
            print("\n📝 Form session ended without completion.")
            if verbose:
                print(f"Final state: {result.get('current_section', 'unknown')}")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Form filling cancelled by user.")
        return False
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point for the CLI application"""
    parser = argparse.ArgumentParser(
        description="CLI Form-Filling Agent powered by LangGraph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_agent.py                    # Start a new form session
  python run_agent.py --verbose          # Start with verbose output
  python run_agent.py --thread-id my123  # Use specific session ID
        """
    )
    
    parser.add_argument(
        "--thread-id",
        type=str,
        help="Specify a custom thread ID for session management"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output for debugging"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Form-Filling Agent v1.0.0"
    )
    
    args = parser.parse_args()
    
    # Display welcome banner
    print_welcome_banner()
    
    # Run the form agent
    success = run_form_agent(
        thread_id=args.thread_id,
        verbose=args.verbose
    )
    
    # Display goodbye message
    print_goodbye_message()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
