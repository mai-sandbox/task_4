"""
CLI Form-Filling Agent using LangGraph

This agent guides users through filling out a form section by section,
using human-in-the-loop controls for interactive CLI input.
"""

from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import sys


class FormState(TypedDict):
    """State schema for the form-filling agent"""
    # Personal Information
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[str]
    
    # Contact Details
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    
    # Preferences
    preferred_contact_method: Optional[str]
    newsletter_subscription: Optional[bool]
    interests: Optional[str]
    
    # Completion tracking
    current_section: str
    completed_sections: list[str]
    form_complete: bool
    
    # Messages for conversation flow
    messages: list


def display_section_header(section_name: str) -> None:
    """Display a formatted header for the current form section"""
    print("\n" + "="*50)
    print(f"  {section_name.upper()}")
    print("="*50)


def get_user_input(prompt: str, required: bool = True) -> str:
    """Get user input with validation"""
    while True:
        try:
            user_input = input(f"{prompt}: ").strip()
            if required and not user_input:
                print("This field is required. Please enter a value.")
                continue
            return user_input
        except KeyboardInterrupt:
            print("\nForm filling cancelled by user.")
            sys.exit(0)
        except EOFError:
            print("\nUnexpected end of input.")
            sys.exit(1)


def validate_email(email: str) -> bool:
    """Basic email validation"""
    return "@" in email and "." in email.split("@")[-1]


def validate_input(field_name: str, value: str) -> bool:
    """Basic input validation for different field types"""
    if field_name == "email":
        return validate_email(value)
    elif field_name == "phone":
        # Basic phone validation - contains digits
        return any(char.isdigit() for char in value)
    return True


def display_form_summary(state: FormState) -> None:
    """Display a summary of all completed form data"""
    print("\n" + "="*50)
    print("  FORM SUMMARY")
    print("="*50)
    
    print("\nPersonal Information:")
    print(f"  Name: {state.get('first_name', 'N/A')} {state.get('last_name', 'N/A')}")
    print(f"  Date of Birth: {state.get('date_of_birth', 'N/A')}")
    
    print("\nContact Details:")
    print(f"  Email: {state.get('email', 'N/A')}")
    print(f"  Phone: {state.get('phone', 'N/A')}")
    print(f"  Address: {state.get('address', 'N/A')}")
    
    print("\nPreferences:")
    print(f"  Preferred Contact: {state.get('preferred_contact_method', 'N/A')}")
    print(f"  Newsletter: {'Yes' if state.get('newsletter_subscription') else 'No'}")
    print(f"  Interests: {state.get('interests', 'N/A')}")
    
    print("\n" + "="*50)


def personal_info_node(state: FormState) -> Dict[str, Any]:
    """Handle personal information section"""
    display_section_header("Personal Information")
    
    print("Please provide your personal information:")
    
    # Get first name
    first_name = get_user_input("First Name", required=True)
    
    # Get last name
    last_name = get_user_input("Last Name", required=True)
    
    # Get date of birth
    date_of_birth = get_user_input("Date of Birth (YYYY-MM-DD)", required=False)
    
    # Update state
    updated_sections = state.get("completed_sections", [])
    if "personal_info" not in updated_sections:
        updated_sections.append("personal_info")
    
    return {
        "first_name": first_name,
        "last_name": last_name,
        "date_of_birth": date_of_birth,
        "current_section": "contact_info",
        "completed_sections": updated_sections,
        "messages": state.get("messages", []) + [{"role": "system", "content": "Personal information collected"}]
    }


def contact_info_node(state: FormState) -> Dict[str, Any]:
    """Handle contact information section"""
    display_section_header("Contact Information")
    
    print("Please provide your contact information:")
    
    # Get email with validation
    while True:
        email = get_user_input("Email Address", required=True)
        if validate_input("email", email):
            break
        print("Please enter a valid email address.")
    
    # Get phone with validation
    while True:
        phone = get_user_input("Phone Number", required=True)
        if validate_input("phone", phone):
            break
        print("Please enter a valid phone number.")
    
    # Get address
    address = get_user_input("Address", required=False)
    
    # Update state
    updated_sections = state.get("completed_sections", [])
    if "contact_info" not in updated_sections:
        updated_sections.append("contact_info")
    
    return {
        "email": email,
        "phone": phone,
        "address": address,
        "current_section": "preferences",
        "completed_sections": updated_sections,
        "messages": state.get("messages", []) + [{"role": "system", "content": "Contact information collected"}]
    }


def preferences_node(state: FormState) -> Dict[str, Any]:
    """Handle preferences section"""
    display_section_header("Preferences")
    
    print("Please specify your preferences:")
    
    # Get preferred contact method
    print("\nPreferred contact method:")
    print("1. Email")
    print("2. Phone")
    print("3. Mail")
    
    while True:
        choice = get_user_input("Choose (1-3)", required=True)
        if choice in ["1", "2", "3"]:
            contact_methods = {"1": "Email", "2": "Phone", "3": "Mail"}
            preferred_contact_method = contact_methods[choice]
            break
        print("Please choose 1, 2, or 3.")
    
    # Get newsletter subscription
    while True:
        newsletter = get_user_input("Subscribe to newsletter? (y/n)", required=True).lower()
        if newsletter in ["y", "yes", "n", "no"]:
            newsletter_subscription = newsletter in ["y", "yes"]
            break
        print("Please enter 'y' for yes or 'n' for no.")
    
    # Get interests
    interests = get_user_input("Interests (optional)", required=False)
    
    # Update state
    updated_sections = state.get("completed_sections", [])
    if "preferences" not in updated_sections:
        updated_sections.append("preferences")
    
    return {
        "preferred_contact_method": preferred_contact_method,
        "newsletter_subscription": newsletter_subscription,
        "interests": interests,
        "current_section": "review",
        "completed_sections": updated_sections,
        "messages": state.get("messages", []) + [{"role": "system", "content": "Preferences collected"}]
    }


def review_node(state: FormState) -> Dict[str, Any]:
    """Handle form review and completion"""
    display_section_header("Review & Submit")
    
    # Display form summary
    display_form_summary(state)
    
    # Ask for confirmation
    while True:
        confirm = get_user_input("\nIs this information correct? (y/n)", required=True).lower()
        if confirm in ["y", "yes"]:
            print("\n✅ Form submitted successfully!")
            return {
                "form_complete": True,
                "current_section": "complete",
                "messages": state.get("messages", []) + [{"role": "system", "content": "Form completed and submitted"}]
            }
        elif confirm in ["n", "no"]:
            print("\nForm submission cancelled. You can restart to fill out the form again.")
            return {
                "form_complete": False,
                "current_section": "cancelled",
                "messages": state.get("messages", []) + [{"role": "system", "content": "Form submission cancelled"}]
            }
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def start_node(state: FormState) -> Dict[str, Any]:
    """Initialize the form-filling process"""
    print("\n🎯 Welcome to the CLI Form Filling Agent!")
    print("This agent will guide you through filling out a form section by section.")
    print("You can press Ctrl+C at any time to cancel.")
    
    return {
        "current_section": "personal_info",
        "completed_sections": [],
        "form_complete": False,
        "messages": [{"role": "system", "content": "Form filling started"}]
    }


# Create the StateGraph
workflow = StateGraph(FormState)

# Add nodes
workflow.add_node("start", start_node)
workflow.add_node("personal_info", personal_info_node)
workflow.add_node("contact_info", contact_info_node)
workflow.add_node("preferences", preferences_node)
workflow.add_node("review", review_node)

# Define the flow
workflow.add_edge(START, "start")
workflow.add_edge("start", "personal_info")
workflow.add_edge("personal_info", "contact_info")
workflow.add_edge("contact_info", "preferences")
workflow.add_edge("preferences", "review")
workflow.add_edge("review", END)

# Add memory for checkpointing
memory = MemorySaver()

# Compile the graph with checkpointing
app = workflow.compile(checkpointer=memory)


if __name__ == "__main__":
    # For testing purposes - run the agent directly
    config = {"configurable": {"thread_id": "form_session_1"}}
    
    try:
        # Initialize empty state
        initial_state = {
            "messages": [],
            "current_section": "",
            "completed_sections": [],
            "form_complete": False
        }
        
        # Run the graph
        result = app.invoke(initial_state, config)
        
        if result.get("form_complete"):
            print("\n🎉 Thank you for completing the form!")
        else:
            print("\n👋 Form filling session ended.")
            
    except KeyboardInterrupt:
        print("\n\n👋 Form filling cancelled. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
