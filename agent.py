from typing import Annotated, Dict, List, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
import json

# Define the form structure
FORM_SECTIONS = {
    "personal_info": {
        "title": "Personal Information",
        "fields": {
            "first_name": {"label": "First Name", "required": True, "type": "text"},
            "last_name": {"label": "Last Name", "required": True, "type": "text"},
            "email": {"label": "Email Address", "required": True, "type": "email"},
            "phone": {"label": "Phone Number", "required": False, "type": "phone"}
        }
    },
    "address": {
        "title": "Address Information",
        "fields": {
            "street": {"label": "Street Address", "required": True, "type": "text"},
            "city": {"label": "City", "required": True, "type": "text"},
            "state": {"label": "State/Province", "required": True, "type": "text"},
            "zip_code": {"label": "ZIP/Postal Code", "required": True, "type": "text"},
            "country": {"label": "Country", "required": True, "type": "text"}
        }
    },
    "preferences": {
        "title": "Preferences",
        "fields": {
            "newsletter": {"label": "Subscribe to newsletter? (y/n)", "required": False, "type": "boolean"},
            "contact_method": {"label": "Preferred contact method (email/phone/mail)", "required": False, "type": "choice", "choices": ["email", "phone", "mail"]},
            "comments": {"label": "Additional comments", "required": False, "type": "text"}
        }
    }
}

class FormState(TypedDict):
    current_section: str
    form_data: Dict[str, Dict[str, Any]]
    completed_sections: List[str]
    user_input: Optional[str]
    current_field: Optional[str]
    validation_errors: List[str]
    is_complete: bool

def validate_field(field_name: str, value: str, field_config: Dict[str, Any]) -> List[str]:
    """Validate a single field value based on its configuration."""
    errors = []
    
    # Check if required field is empty
    if field_config.get("required", False) and not value.strip():
        errors.append(f"{field_config['label']} is required")
        return errors
    
    # Skip validation for empty optional fields
    if not value.strip():
        return errors
    
    # Type-specific validation
    field_type = field_config.get("type", "text")
    
    if field_type == "email":
        if "@" not in value or "." not in value.split("@")[-1]:
            errors.append(f"{field_config['label']} must be a valid email address")
    
    elif field_type == "phone":
        # Simple phone validation - contains only digits, spaces, dashes, parentheses
        import re
        if not re.match(r'^[\d\s\-\(\)\+]+$', value):
            errors.append(f"{field_config['label']} must be a valid phone number")
    
    elif field_type == "boolean":
        if value.lower() not in ["y", "n", "yes", "no", "true", "false"]:
            errors.append(f"{field_config['label']} must be y/n, yes/no, or true/false")
    
    elif field_type == "choice":
        choices = field_config.get("choices", [])
        if value.lower() not in [choice.lower() for choice in choices]:
            errors.append(f"{field_config['label']} must be one of: {', '.join(choices)}")
    
    return errors

def display_form_node(state: FormState) -> Dict[str, Any]:
    """Display the current form section and prompt for user input."""
    current_section = state.get("current_section")
    
    if not current_section:
        # Start with the first section
        section_names = list(FORM_SECTIONS.keys())
        current_section = section_names[0]
        return {
            "current_section": current_section,
            "form_data": {section: {} for section in section_names},
            "completed_sections": [],
            "validation_errors": [],
            "is_complete": False
        }
    
    # Check if form is complete
    if len(state.get("completed_sections", [])) == len(FORM_SECTIONS):
        return {"is_complete": True}
    
    section_config = FORM_SECTIONS[current_section]
    form_data = state.get("form_data", {})
    section_data = form_data.get(current_section, {})
    
    # Display section header
    display_text = f"\n{'='*50}\n"
    display_text += f"SECTION: {section_config['title']}\n"
    display_text += f"{'='*50}\n"
    
    # Show validation errors if any
    validation_errors = state.get("validation_errors", [])
    if validation_errors:
        display_text += "\n❌ VALIDATION ERRORS:\n"
        for error in validation_errors:
            display_text += f"  • {error}\n"
        display_text += "\n"
    
    # Display current section progress
    completed_fields = []
    remaining_fields = []
    
    for field_name, field_config in section_config["fields"].items():
        if field_name in section_data and section_data[field_name]:
            completed_fields.append(f"✅ {field_config['label']}: {section_data[field_name]}")
        else:
            required_marker = " *" if field_config.get("required", False) else ""
            remaining_fields.append(f"⏳ {field_config['label']}{required_marker}")
    
    if completed_fields:
        display_text += "COMPLETED FIELDS:\n"
        for field in completed_fields:
            display_text += f"  {field}\n"
        display_text += "\n"
    
    if remaining_fields:
        display_text += "REMAINING FIELDS:\n"
        for field in remaining_fields:
            display_text += f"  {field}\n"
        display_text += "\n"
    
    # Find next field to fill
    current_field = None
    for field_name, field_config in section_config["fields"].items():
        if field_name not in section_data or not section_data[field_name]:
            current_field = field_name
            break
    
    if current_field:
        field_config = section_config["fields"][current_field]
        prompt = f"Enter {field_config['label']}"
        if field_config.get("required", False):
            prompt += " *"
        if field_config.get("type") == "choice":
            prompt += f" ({'/'.join(field_config.get('choices', []))})"
        prompt += ": "
        
        display_text += f"NEXT FIELD: {prompt}"
        
        # Use interrupt to get user input
        user_response = interrupt({"prompt": display_text + prompt})
        user_input = user_response if isinstance(user_response, str) else user_response.get("input", "")
        
        return {
            "current_field": current_field,
            "user_input": user_input
        }
    else:
        # All fields in section are complete
        return {"current_field": None}

def collect_section_data_node(state: FormState) -> Dict[str, Any]:
    """Collect and store user input for the current field."""
    current_section = state.get("current_section")
    current_field = state.get("current_field")
    user_input = state.get("user_input", "")
    
    if not current_section or not current_field:
        return {}
    
    # Update form data with user input
    form_data = state.get("form_data", {}).copy()
    if current_section not in form_data:
        form_data[current_section] = {}
    
    form_data[current_section][current_field] = user_input.strip()
    
    return {
        "form_data": form_data,
        "user_input": None,
        "current_field": None
    }

def validate_input_node(state: FormState) -> Dict[str, Any]:
    """Validate the current section's data."""
    current_section = state.get("current_section")
    form_data = state.get("form_data", {})
    
    if not current_section or current_section not in form_data:
        return {"validation_errors": []}
    
    section_config = FORM_SECTIONS[current_section]
    section_data = form_data[current_section]
    errors = []
    
    # Validate each field in the current section
    for field_name, field_config in section_config["fields"].items():
        value = section_data.get(field_name, "")
        field_errors = validate_field(field_name, value, field_config)
        errors.extend(field_errors)
    
    return {"validation_errors": errors}

def move_to_next_section_node(state: FormState) -> Dict[str, Any]:
    """Move to the next section or complete the form."""
    current_section = state.get("current_section")
    completed_sections = state.get("completed_sections", []).copy()
    validation_errors = state.get("validation_errors", [])
    
    # If there are validation errors, stay in current section
    if validation_errors:
        return {}
    
    # Mark current section as completed
    if current_section and current_section not in completed_sections:
        completed_sections.append(current_section)
    
    # Find next section
    section_names = list(FORM_SECTIONS.keys())
    try:
        current_index = section_names.index(current_section)
        if current_index + 1 < len(section_names):
            next_section = section_names[current_index + 1]
            return {
                "current_section": next_section,
                "completed_sections": completed_sections
            }
        else:
            # All sections completed
            return {
                "completed_sections": completed_sections,
                "is_complete": True
            }
    except ValueError:
        # Current section not found, start from beginning
        return {
            "current_section": section_names[0],
            "completed_sections": completed_sections
        }

def should_continue(state: FormState) -> str:
    """Determine the next node based on current state."""
    if state.get("is_complete", False):
        return "end"
    
    validation_errors = state.get("validation_errors", [])
    current_field = state.get("current_field")
    
    if validation_errors:
        return "display_form"
    elif current_field:
        return "collect_data"
    else:
        return "validate_input"

# Create the StateGraph
graph_builder = StateGraph(FormState)

# Add nodes
graph_builder.add_node("display_form", display_form_node)
graph_builder.add_node("collect_data", collect_section_data_node)
graph_builder.add_node("validate_input", validate_input_node)
graph_builder.add_node("move_to_next", move_to_next_section_node)

# Add edges
graph_builder.add_edge(START, "display_form")
graph_builder.add_conditional_edges(
    "display_form",
    should_continue,
    {
        "collect_data": "collect_data",
        "validate_input": "validate_input",
        "end": END
    }
)
graph_builder.add_edge("collect_data", "display_form")
graph_builder.add_edge("validate_input", "move_to_next")
graph_builder.add_edge("move_to_next", "display_form")

# Compile the graph
graph = graph_builder.compile()

# Export as 'app' for LangGraph deployment
app = graph

def run_cli_form():
    """Run the form-filling agent in CLI mode."""
    print("🎯 Welcome to the CLI Form-Filling Agent!")
    print("📝 Please fill out the form section by section.")
    print("💡 Type 'quit' or 'exit' at any time to stop.\n")
    
    config = {"configurable": {"thread_id": "cli_session"}}
    
    try:
        # Start the form-filling process
        for event in graph.stream({}, config, stream_mode="values"):
            # The display and interaction happen through the interrupt mechanism
            pass
        
        # Get final state
        final_state = graph.get_state(config)
        
        if final_state.values.get("is_complete", False):
            print("\n🎉 Form completed successfully!")
            print("\n📋 FORM SUMMARY:")
            print("="*50)
            
            form_data = final_state.values.get("form_data", {})
            for section_name, section_data in form_data.items():
                section_config = FORM_SECTIONS[section_name]
                print(f"\n{section_config['title']}:")
                for field_name, value in section_data.items():
                    if value:
                        field_config = section_config["fields"][field_name]
                        print(f"  {field_config['label']}: {value}")
            
            # Save to file
            with open("completed_form.json", "w") as f:
                json.dump(form_data, f, indent=2)
            print(f"\n💾 Form data saved to 'completed_form.json'")
        
    except KeyboardInterrupt:
        print("\n\n👋 Form filling cancelled by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    run_cli_form()
