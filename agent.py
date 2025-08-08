"""
CLI Form-Filling Agent using LangGraph

This agent processes forms section by section, using human-in-the-loop controls
to collect user input via CLI interrupts. The agent maintains state across
interruptions and provides a structured workflow for form completion.
"""

from typing import Dict, Any, Literal, Optional
from typing_extensions import TypedDict
from dataclasses import dataclass

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.tools import tool


# Form State Schema
class FormState(TypedDict):
    """State schema for the form-filling agent."""
    form_data: Dict[str, Any]  # Stores all collected form data
    current_section: str       # Tracks current form section
    completed_sections: list[str]  # List of completed sections
    is_complete: bool         # Whether form is fully completed


# Form section definitions
FORM_SECTIONS = {
    "personal_info": {
        "title": "Personal Information",
        "fields": [
            {"name": "first_name", "prompt": "Enter your first name", "required": True},
            {"name": "last_name", "prompt": "Enter your last name", "required": True},
            {"name": "date_of_birth", "prompt": "Enter your date of birth (YYYY-MM-DD)", "required": True},
            {"name": "phone", "prompt": "Enter your phone number", "required": False},
        ]
    },
    "contact_info": {
        "title": "Contact Information", 
        "fields": [
            {"name": "email", "prompt": "Enter your email address", "required": True},
            {"name": "address", "prompt": "Enter your street address", "required": True},
            {"name": "city", "prompt": "Enter your city", "required": True},
            {"name": "state", "prompt": "Enter your state/province", "required": True},
            {"name": "zip_code", "prompt": "Enter your ZIP/postal code", "required": True},
        ]
    },
    "preferences": {
        "title": "Preferences",
        "fields": [
            {"name": "newsletter", "prompt": "Subscribe to newsletter? (yes/no)", "required": False},
            {"name": "contact_method", "prompt": "Preferred contact method (email/phone/mail)", "required": False},
            {"name": "interests", "prompt": "Areas of interest (comma-separated)", "required": False},
        ]
    }
}

SECTION_ORDER = ["personal_info", "contact_info", "preferences", "review"]


def collect_section_data(section_name: str, section_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Function to collect data for a specific form section using interrupt.
    
    Args:
        section_name: Name of the form section
        section_config: Configuration for the section including fields
        
    Returns:
        Dictionary containing collected field data
    """
    # Prepare the interrupt payload with section information
    interrupt_data = {
        "action": "collect_section_data",
        "section_name": section_name,
        "section_title": section_config["title"],
        "fields": section_config["fields"]
    }
    
    # Interrupt execution to collect user input via CLI
    collected_data = interrupt(interrupt_data)
    
    return collected_data


def start_form(state: FormState) -> FormState:
    """Initialize the form-filling process."""
    return {
        "form_data": state.get("form_data", {}),
        "current_section": "personal_info",
        "completed_sections": [],
        "is_complete": False
    }


def personal_info_section(state: FormState) -> FormState:
    """Process personal information section."""
    section_name = "personal_info"
    section_config = FORM_SECTIONS[section_name]
    
    # Collect data for this section
    section_data = collect_section_data(section_name, section_config)
    
    # Update form data with collected information
    updated_form_data = state["form_data"].copy()
    updated_form_data.update(section_data)
    
    # Update completed sections
    completed = state["completed_sections"].copy()
    if section_name not in completed:
        completed.append(section_name)
    
    return {
        "form_data": updated_form_data,
        "current_section": "contact_info",
        "completed_sections": completed,
        "is_complete": False
    }


def contact_info_section(state: FormState) -> FormState:
    """Process contact information section."""
    section_name = "contact_info"
    section_config = FORM_SECTIONS[section_name]
    
    # Collect data for this section
    section_data = collect_section_data(section_name, section_config)
    
    # Update form data with collected information
    updated_form_data = state["form_data"].copy()
    updated_form_data.update(section_data)
    
    # Update completed sections
    completed = state["completed_sections"].copy()
    if section_name not in completed:
        completed.append(section_name)
    
    return {
        "form_data": updated_form_data,
        "current_section": "preferences",
        "completed_sections": completed,
        "is_complete": False
    }


def preferences_section(state: FormState) -> FormState:
    """Process preferences section."""
    section_name = "preferences"
    section_config = FORM_SECTIONS[section_name]
    
    # Collect data for this section
    section_data = collect_section_data(section_name, section_config)
    
    # Update form data with collected information
    updated_form_data = state["form_data"].copy()
    updated_form_data.update(section_data)
    
    # Update completed sections
    completed = state["completed_sections"].copy()
    if section_name not in completed:
        completed.append(section_name)
    
    return {
        "form_data": updated_form_data,
        "current_section": "review",
        "completed_sections": completed,
        "is_complete": False
    }


def review_section(state: FormState) -> FormState:
    """Review and finalize the form."""
    # Prepare review data for user confirmation
    interrupt_data = {
        "action": "review_form",
        "form_data": state["form_data"],
        "completed_sections": state["completed_sections"]
    }
    
    # Show form data for review and get confirmation
    confirmation = interrupt(interrupt_data)
    
    # Update completed sections
    completed = state["completed_sections"].copy()
    if "review" not in completed:
        completed.append("review")
    
    return {
        "form_data": state["form_data"],
        "current_section": "complete",
        "completed_sections": completed,
        "is_complete": confirmation.get("confirmed", False)
    }


def complete_form(state: FormState) -> FormState:
    """Mark the form as completed."""
    return {
        "form_data": state["form_data"],
        "current_section": "complete",
        "completed_sections": state["completed_sections"],
        "is_complete": True
    }


def route_next_section(state: FormState) -> Literal["personal_info", "contact_info", "preferences", "review", "complete", END]:
    """
    Conditional routing function to determine the next section.
    
    Args:
        state: Current form state
        
    Returns:
        Name of the next node to execute
    """
    current_section = state.get("current_section", "personal_info")
    
    if current_section == "personal_info":
        return "personal_info"
    elif current_section == "contact_info":
        return "contact_info"
    elif current_section == "preferences":
        return "preferences"
    elif current_section == "review":
        return "review"
    elif current_section == "complete":
        if state.get("is_complete", False):
            return "complete"
        else:
            # If not confirmed, go back to review
            return "review"
    else:
        return END


def should_end(state: FormState) -> Literal["complete", END]:
    """Determine if the form process should end."""
    if state.get("is_complete", False):
        return END
    else:
        return "complete"


# Build the StateGraph
def create_form_agent():
    """Create and compile the form-filling agent graph."""
    
    # Initialize the StateGraph with FormState schema
    graph_builder = StateGraph(FormState)
    
    # Add nodes for each form section
    graph_builder.add_node("start", start_form)
    graph_builder.add_node("personal_info", personal_info_section)
    graph_builder.add_node("contact_info", contact_info_section)
    graph_builder.add_node("preferences", preferences_section)
    graph_builder.add_node("review", review_section)
    graph_builder.add_node("complete", complete_form)
    
    # Add edges and conditional routing
    graph_builder.add_edge(START, "start")
    graph_builder.add_conditional_edges("start", route_next_section)
    graph_builder.add_conditional_edges("personal_info", route_next_section)
    graph_builder.add_conditional_edges("contact_info", route_next_section)
    graph_builder.add_conditional_edges("preferences", route_next_section)
    graph_builder.add_conditional_edges("review", route_next_section)
    graph_builder.add_conditional_edges("complete", should_end)
    
    # Compile the graph with checkpointer for interrupt support
    checkpointer = InMemorySaver()
    compiled_graph = graph_builder.compile(checkpointer=checkpointer)
    
    return compiled_graph


# Export the compiled graph as 'app' (required for LangGraph deployment)
app = create_form_agent()


if __name__ == "__main__":
    # Basic test to verify graph compilation
    print("Form-filling agent compiled successfully!")
    print(f"Graph nodes: {list(app.get_graph().nodes.keys())}")
    print("Ready for CLI interaction...")

