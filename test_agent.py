#!/usr/bin/env python3
"""Test script for the form filling agent"""

from agent import app, initialize_form


def test_form_agent():
    """Test the form agent with sample data"""
    
    print("\n" + "="*50)
    print("🧪 TESTING FORM AGENT")
    print("="*50)
    
    initial_state = {
        "messages": [],
        "current_section": None,
        "sections": initialize_form(),
        "form_data": {},
        "completed_sections": [],
        "all_complete": False
    }
    
    print("\nInitial State:")
    print(f"- Sections: {[s['name'] for s in initial_state['sections']]}")
    print(f"- Completed sections: {initial_state['completed_sections']}")
    print(f"- All complete: {initial_state['all_complete']}")
    
    print("\n✅ Form agent created successfully!")
    print("\nThe agent has the following sections:")
    for i, section in enumerate(initial_state["sections"], 1):
        print(f"\n{i}. {section['name']}:")
        for field in section["fields"]:
            print(f"   - {field['name']}: {field['prompt']}")
    
    print("\n" + "="*50)
    print("To run the interactive form:")
    print("  python agent.py")
    print("\nThe agent will guide you through each section,")
    print("collecting input for each field, and provide a")
    print("summary at the end with an option to save.")
    print("="*50)


if __name__ == "__main__":
    test_form_agent()