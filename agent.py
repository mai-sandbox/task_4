"""
CLI Form-Filling Agent using LangGraph

This agent guides users through filling out a form section by section using CLI interaction.
It uses LangGraph's StateGraph with human-in-the-loop functionality to pause execution
and collect user input for each form section.
"""

from typing import TypedDict, Literal, Optional, Dict, Any
from langgraph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import interrupt
import json
import re
from datetime import datetime


class FormState(TypedDict):
    """Custom state schema to track form filling progress"""
    current_section: str
    form_data: Dict[str, Any]
    sections_completed: list[str]
    is_complete: bool
    user_input: Optional[str]
    validation_errors: list[str]


def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}


def collect_personal_info(state: FormState) -> FormState:
    """Node to collect personal information from user"""
    print("\n=== PERSONAL INFORMATION SECTION ===")
    
    # Check if we already have this data and user wants to edit
    if "personal_info" in state.get("form_data", {}) and state.get("user_input") != "edit":
        print("Current personal information:")
        for key, value in state["form_data"]["personal_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\nPress Enter to continue or type 'edit' to modify this section")
        
        # Use interrupt to pause and wait for user input
        user_choice = interrupt("Continue or edit personal info? (press Enter to continue, 'edit' to modify): ")
        
        if user_choice and user_choice.strip().lower() == "edit":
            # Clear existing data to re-collect
            form_data = state.get("form_data", {})
            if "personal_info" in form_data:
                del form_data["personal_info"]
            return {
                **state,
                "form_data": form_data,
                "current_section": "personal_info",
                "user_input": "edit"
            }
        else:
            # Mark section as completed and move on
            sections_completed = state.get("sections_completed", [])
            if "personal_info" not in sections_completed:
                sections_completed.append("personal_info")
            return {
                **state,
                "sections_completed": sections_completed,
                "current_section": "personal_info",
                "user_input": None
            }
    
    # Collect personal information
    print("Please provide the following information:")
    personal_info = {}
    validation_errors = []
    
    # Collect Full Name
    print("\n1. Full Name:")
    full_name = interrupt("Enter your full name: ")
    if not full_name or len(full_name.strip()) < 2:
        validation_errors.append("Full name must be at least 2 characters long")
    else:
        personal_info["full_name"] = full_name.strip()
    
    # Collect Date of Birth
    print("\n2. Date of Birth (YYYY-MM-DD):")
    dob = interrupt("Enter your date of birth (YYYY-MM-DD): ")
    if not validate_date(dob):
        validation_errors.append("Date of birth must be in YYYY-MM-DD format and be a valid date")
    else:
        personal_info["date_of_birth"] = dob.strip()
    
    # Collect Email
    print("\n3. Email Address:")
    email = interrupt("Enter your email address: ")
    if not validate_email(email):
        validation_errors.append("Please enter a valid email address")
    else:
        personal_info["email"] = email.strip().lower()
    
    # Collect Phone Number
    print("\n4. Phone Number:")
    phone = interrupt("Enter your phone number: ")
    if not validate_phone(phone):
        validation_errors.append("Please enter a valid phone number")
    else:
        personal_info["phone"] = phone.strip()
    
    # Handle validation errors
    if validation_errors:
        print("\n❌ Validation Errors:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\nPlease correct the errors and try again.")
        return {
            **state,
            "current_section": "personal_info",
            "validation_errors": validation_errors,
            "user_input": None
        }
    
    # Update state with collected data
    form_data = state.get("form_data", {})
    form_data["personal_info"] = personal_info
    sections_completed = state.get("sections_completed", [])
    if "personal_info" not in sections_completed:
        sections_completed.append("personal_info")
    
    print("\n✅ Personal information collected successfully!")
    
    return {
        **state,
        "form_data": form_data,
        "sections_completed": sections_completed,
        "current_section": "personal_info",
        "validation_errors": [],
        "user_input": None
    }


def collect_contact_info(state: FormState) -> FormState:
    """Node to collect contact information from user"""
    print("\n=== CONTACT INFORMATION SECTION ===")
    print("Please provide the following contact details:")
    
    # Check if we already have this data
    if "contact_info" in state.get("form_data", {}):
        print("Current contact information:")
        for key, value in state["form_data"]["contact_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\nPress Enter to continue or type 'edit' to modify:")
        
        return {
            **state,
            "current_section": "contact_info",
            "user_input": None
        }
    
    print("1. Street Address:")
    print("2. City:")
    print("3. State/Province:")
    print("4. ZIP/Postal Code:")
    print("5. Country:")
    print("\nPlease provide your input (the agent will pause here for CLI interaction)")
    
    return {
        **state,
        "current_section": "contact_info",
        "user_input": None
    }


def collect_preferences(state: FormState) -> FormState:
    """Node to collect user preferences"""
    print("\n=== PREFERENCES SECTION ===")
    print("Please specify your preferences:")
    
    # Check if we already have this data
    if "preferences" in state.get("form_data", {}):
        print("Current preferences:")
        for key, value in state["form_data"]["preferences"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\nPress Enter to continue or type 'edit' to modify:")
        
        return {
            **state,
            "current_section": "preferences",
            "user_input": None
        }
    
    print("1. Preferred Contact Method (email/phone/mail):")
    print("2. Newsletter Subscription (yes/no):")
    print("3. Language Preference:")
    print("4. Special Requirements (optional):")
    print("\nPlease provide your input (the agent will pause here for CLI interaction)")
    
    return {
        **state,
        "current_section": "preferences",
        "user_input": None
    }


def review_form(state: FormState) -> FormState:
    """Node to review all collected information"""
    print("\n=== FORM REVIEW ===")
    print("Please review all the information you've provided:")
    
    form_data = state.get("form_data", {})
    
    if "personal_info" in form_data:
        print("\nPersonal Information:")
        for key, value in form_data["personal_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if "contact_info" in form_data:
        print("\nContact Information:")
        for key, value in form_data["contact_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if "preferences" in form_data:
        print("\nPreferences:")
        for key, value in form_data["preferences"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\nOptions:")
    print("1. Submit form (type 'submit')")
    print("2. Edit personal info (type 'edit_personal')")
    print("3. Edit contact info (type 'edit_contact')")
    print("4. Edit preferences (type 'edit_preferences')")
    print("\nPlease choose an option:")
    
    return {
        **state,
        "current_section": "review",
        "user_input": None
    }


def submit_form(state: FormState) -> FormState:
    """Node to handle form submission"""
    print("\n=== FORM SUBMISSION ===")
    print("✅ Form submitted successfully!")
    print("\nThank you for completing the form. Your information has been recorded.")
    
    # Display final summary
    print("\n--- SUBMISSION SUMMARY ---")
    form_data = state.get("form_data", {})
    print(json.dumps(form_data, indent=2))
    
    return {
        **state,
        "current_section": "complete",
        "is_complete": True,
        "sections_completed": state.get("sections_completed", []) + ["submit"]
    }


def determine_next_section(state: FormState) -> str:
    """Conditional edge function to determine the next section"""
    current_section = state.get("current_section", "")
    sections_completed = state.get("sections_completed", [])
    user_input = state.get("user_input", "")
    
    # Handle review section navigation
    if current_section == "review":
        if user_input == "submit":
            return "submit"
        elif user_input == "edit_personal":
            return "personal_info"
        elif user_input == "edit_contact":
            return "contact_info"
        elif user_input == "edit_preferences":
            return "preferences"
        else:
            return "submit"  # Default to submit if unclear
    
    # Sequential progression through sections
    if current_section == "personal_info" and "personal_info" not in sections_completed:
        return "contact_info"
    elif current_section == "contact_info" and "contact_info" not in sections_completed:
        return "preferences"
    elif current_section == "preferences" and "preferences" not in sections_completed:
        return "review"
    elif current_section == "submit":
        return END
    
    # Default progression
    if "personal_info" not in sections_completed:
        return "personal_info"
    elif "contact_info" not in sections_completed:
        return "contact_info"
    elif "preferences" not in sections_completed:
        return "preferences"
    else:
        return "review"


def should_end(state: FormState) -> bool:
    """Check if the form filling process should end"""
    return state.get("is_complete", False)


# Create the StateGraph
workflow = StateGraph(FormState)

# Add nodes
workflow.add_node("personal_info", collect_personal_info)
workflow.add_node("contact_info", collect_contact_info)
workflow.add_node("preferences", collect_preferences)
workflow.add_node("review", review_form)
workflow.add_node("submit", submit_form)

# Add edges
workflow.add_edge(START, "personal_info")
workflow.add_conditional_edges(
    "personal_info",
    determine_next_section,
    {
        "contact_info": "contact_info",
        "personal_info": "personal_info",
        "review": "review"
    }
)
workflow.add_conditional_edges(
    "contact_info",
    determine_next_section,
    {
        "preferences": "preferences",
        "contact_info": "contact_info",
        "personal_info": "personal_info",
        "review": "review"
    }
)
workflow.add_conditional_edges(
    "preferences",
    determine_next_section,
    {
        "review": "review",
        "preferences": "preferences",
        "personal_info": "personal_info",
        "contact_info": "contact_info"
    }
)
workflow.add_conditional_edges(
    "review",
    determine_next_section,
    {
        "submit": "submit",
        "personal_info": "personal_info",
        "contact_info": "contact_info",
        "preferences": "preferences"
    }
)
workflow.add_edge("submit", END)

# Compile the graph and export as 'app' as required by LangGraph
app = workflow.compile(
    # Enable human-in-the-loop functionality
    interrupt_before=["personal_info", "contact_info", "preferences", "review"],
    checkpointer=None  # Can be configured for persistence if needed
)

# Initialize default state
def get_initial_state() -> FormState:
    """Get the initial state for the form filling process"""
    return FormState(
        current_section="personal_info",
        form_data={},
        sections_completed=[],
        is_complete=False,
        user_input=None,
        validation_errors=[]
    )


if __name__ == "__main__":
    print("CLI Form-Filling Agent")
    print("This agent will guide you through filling out a form section by section.")
    print("The agent uses LangGraph with human-in-the-loop functionality.")
    print("\nTo run this agent, use the LangGraph CLI or integrate it into your application.")



    return re.match(pattern, email.strip()) is not None


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    if not phone:
        return False
    # Remove common separators and spaces
    cleaned = re.sub(r'[\s\-\(\)\+\.]', '', phone.strip())
    # Check if it contains only digits and is reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def validate_date(date_str: str) -> bool:
    """Validate date in YYYY-MM-DD format"""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str.strip(), '%Y-%m-%d')
        return True
    except ValueError:
        return False


def collect_personal_info(state: FormState) -> FormState:
    """Node to collect personal information from user"""
    print("\n=== PERSONAL INFORMATION SECTION ===")
    
    # Check if we already have this data and user wants to edit
    if "personal_info" in state.get("form_data", {}) and state.get("user_input") != "edit":
        print("Current personal information:")
        for key, value in state["form_data"]["personal_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\nPress Enter to continue or type 'edit' to modify this section")
        
        # Use interrupt to pause and wait for user input
        user_choice = interrupt("Continue or edit personal info? (press Enter to continue, 'edit' to modify): ")
        
        if user_choice and user_choice.strip().lower() == "edit":
            # Clear existing data to re-collect
            form_data = state.get("form_data", {})
            if "personal_info" in form_data:
                del form_data["personal_info"]
            return {
                **state,
                "form_data": form_data,
                "current_section": "personal_info",
                "user_input": "edit"
            }
        else:
            # Mark section as completed and move on
            sections_completed = state.get("sections_completed", [])
            if "personal_info" not in sections_completed:
                sections_completed.append("personal_info")
            return {
                **state,
                "sections_completed": sections_completed,
                "current_section": "personal_info",
                "user_input": None
            }
    
    # Collect personal information
    print("Please provide the following information:")
    personal_info = {}
    validation_errors = []
    
    # Collect Full Name
    print("\n1. Full Name:")
    full_name = interrupt("Enter your full name: ")
    if not full_name or len(full_name.strip()) < 2:
        validation_errors.append("Full name must be at least 2 characters long")
    else:
        personal_info["full_name"] = full_name.strip()
    
    # Collect Date of Birth
    print("\n2. Date of Birth (YYYY-MM-DD):")
    dob = interrupt("Enter your date of birth (YYYY-MM-DD): ")
    if not validate_date(dob):
        validation_errors.append("Date of birth must be in YYYY-MM-DD format and be a valid date")
    else:
        personal_info["date_of_birth"] = dob.strip()
    
    # Collect Email
    print("\n3. Email Address:")
    email = interrupt("Enter your email address: ")
    if not validate_email(email):
        validation_errors.append("Please enter a valid email address")
    else:
        personal_info["email"] = email.strip().lower()
    
    # Collect Phone Number
    print("\n4. Phone Number:")
    phone = interrupt("Enter your phone number: ")
    if not validate_phone(phone):
        validation_errors.append("Please enter a valid phone number")
    else:
        personal_info["phone"] = phone.strip()
    
    # Handle validation errors
    if validation_errors:
        print("\n❌ Validation Errors:")
        for error in validation_errors:
            print(f"  - {error}")
        print("\nPlease correct the errors and try again.")
        return {
            **state,
            "current_section": "personal_info",
            "validation_errors": validation_errors,
            "user_input": None
        }
    
    # Update state with collected data
    form_data = state.get("form_data", {})
    form_data["personal_info"] = personal_info
    sections_completed = state.get("sections_completed", [])
    if "personal_info" not in sections_completed:
        sections_completed.append("personal_info")
    
    print("\n✅ Personal information collected successfully!")
    
    return {
        **state,
        "form_data": form_data,
        "sections_completed": sections_completed,
        "current_section": "personal_info",
        "validation_errors": [],
        "user_input": None
    }


def collect_contact_info(state: FormState) -> FormState:
    """Node to collect contact information from user"""
    print("\n=== CONTACT INFORMATION SECTION ===")
    print("Please provide the following contact details:")
    
    # Check if we already have this data
    if "contact_info" in state.get("form_data", {}):
        print("Current contact information:")
        for key, value in state["form_data"]["contact_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\nPress Enter to continue or type 'edit' to modify:")
        
        return {
            **state,
            "current_section": "contact_info",
            "user_input": None
        }
    
    print("1. Street Address:")
    print("2. City:")
    print("3. State/Province:")
    print("4. ZIP/Postal Code:")
    print("5. Country:")
    print("\nPlease provide your input (the agent will pause here for CLI interaction)")
    
    return {
        **state,
        "current_section": "contact_info",
        "user_input": None
    }


def collect_preferences(state: FormState) -> FormState:
    """Node to collect user preferences"""
    print("\n=== PREFERENCES SECTION ===")
    print("Please specify your preferences:")
    
    # Check if we already have this data
    if "preferences" in state.get("form_data", {}):
        print("Current preferences:")
        for key, value in state["form_data"]["preferences"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print("\nPress Enter to continue or type 'edit' to modify:")
        
        return {
            **state,
            "current_section": "preferences",
            "user_input": None
        }
    
    print("1. Preferred Contact Method (email/phone/mail):")
    print("2. Newsletter Subscription (yes/no):")
    print("3. Language Preference:")
    print("4. Special Requirements (optional):")
    print("\nPlease provide your input (the agent will pause here for CLI interaction)")
    
    return {
        **state,
        "current_section": "preferences",
        "user_input": None
    }


def review_form(state: FormState) -> FormState:
    """Node to review all collected information"""
    print("\n=== FORM REVIEW ===")
    print("Please review all the information you've provided:")
    
    form_data = state.get("form_data", {})
    
    if "personal_info" in form_data:
        print("\nPersonal Information:")
        for key, value in form_data["personal_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if "contact_info" in form_data:
        print("\nContact Information:")
        for key, value in form_data["contact_info"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    if "preferences" in form_data:
        print("\nPreferences:")
        for key, value in form_data["preferences"].items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\nOptions:")
    print("1. Submit form (type 'submit')")
    print("2. Edit personal info (type 'edit_personal')")
    print("3. Edit contact info (type 'edit_contact')")
    print("4. Edit preferences (type 'edit_preferences')")
    print("\nPlease choose an option:")
    
    return {
        **state,
        "current_section": "review",
        "user_input": None
    }


def submit_form(state: FormState) -> FormState:
    """Node to handle form submission"""
    print("\n=== FORM SUBMISSION ===")
    print("✅ Form submitted successfully!")
    print("\nThank you for completing the form. Your information has been recorded.")
    
    # Display final summary
    print("\n--- SUBMISSION SUMMARY ---")
    form_data = state.get("form_data", {})
    print(json.dumps(form_data, indent=2))
    
    return {
        **state,
        "current_section": "complete",
        "is_complete": True,
        "sections_completed": state.get("sections_completed", []) + ["submit"]
    }


def determine_next_section(state: FormState) -> str:
    """Conditional edge function to determine the next section"""
    current_section = state.get("current_section", "")
    sections_completed = state.get("sections_completed", [])
    user_input = state.get("user_input", "")
    
    # Handle review section navigation
    if current_section == "review":
        if user_input == "submit":
            return "submit"
        elif user_input == "edit_personal":
            return "personal_info"
        elif user_input == "edit_contact":
            return "contact_info"
        elif user_input == "edit_preferences":
            return "preferences"
        else:
            return "submit"  # Default to submit if unclear
    
    # Sequential progression through sections
    if current_section == "personal_info" and "personal_info" not in sections_completed:
        return "contact_info"
    elif current_section == "contact_info" and "contact_info" not in sections_completed:
        return "preferences"
    elif current_section == "preferences" and "preferences" not in sections_completed:
        return "review"
    elif current_section == "submit":
        return END
    
    # Default progression
    if "personal_info" not in sections_completed:
        return "personal_info"
    elif "contact_info" not in sections_completed:
        return "contact_info"
    elif "preferences" not in sections_completed:
        return "preferences"
    else:
        return "review"


def should_end(state: FormState) -> bool:
    """Check if the form filling process should end"""
    return state.get("is_complete", False)


# Create the StateGraph
workflow = StateGraph(FormState)

# Add nodes
workflow.add_node("personal_info", collect_personal_info)
workflow.add_node("contact_info", collect_contact_info)
workflow.add_node("preferences", collect_preferences)
workflow.add_node("review", review_form)
workflow.add_node("submit", submit_form)

# Add edges
workflow.add_edge(START, "personal_info")
workflow.add_conditional_edges(
    "personal_info",
    determine_next_section,
    {
        "contact_info": "contact_info",
        "personal_info": "personal_info",
        "review": "review"
    }
)
workflow.add_conditional_edges(
    "contact_info",
    determine_next_section,
    {
        "preferences": "preferences",
        "contact_info": "contact_info",
        "personal_info": "personal_info",
        "review": "review"
    }
)
workflow.add_conditional_edges(
    "preferences",
    determine_next_section,
    {
        "review": "review",
        "preferences": "preferences",
        "personal_info": "personal_info",
        "contact_info": "contact_info"
    }
)
workflow.add_conditional_edges(
    "review",
    determine_next_section,
    {
        "submit": "submit",
        "personal_info": "personal_info",
        "contact_info": "contact_info",
        "preferences": "preferences"
    }
)
workflow.add_edge("submit", END)

# Compile the graph and export as 'app' as required by LangGraph
app = workflow.compile(
    # Enable human-in-the-loop functionality
    interrupt_before=["personal_info", "contact_info", "preferences", "review"],
    checkpointer=None  # Can be configured for persistence if needed
)

# Initialize default state
def get_initial_state() -> FormState:
    """Get the initial state for the form filling process"""
    return FormState(
        current_section="personal_info",
        form_data={},
        sections_completed=[],
        is_complete=False,
        user_input=None,
        validation_errors=[]
    )


if __name__ == "__main__":
    print("CLI Form-Filling Agent")
    print("This agent will guide you through filling out a form section by section.")
    print("The agent uses LangGraph with human-in-the-loop functionality.")
    print("\nTo run this agent, use the LangGraph CLI or integrate it into your application.")






