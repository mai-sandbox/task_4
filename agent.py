"""
CLI Form-Filling Agent using LangGraph

This agent guides users through filling out a multi-section form using
human-in-the-loop interactions via the CLI.
"""

from typing import Annotated, Dict, List, Any, Optional, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


# State definition for the form-filling agent
class FormState(TypedDict):
    """State tracking form completion progress and user responses."""
    # Form structure and navigation
    current_section: int
    total_sections: int
    section_names: List[str]
    
    # User responses storage
    responses: Dict[str, Any]
    
    # Form completion tracking
    is_complete: bool
    validation_errors: List[str]
    
    # Current field being processed
    current_field: Optional[str]
    current_question: Optional[str]


# Form structure definition
FORM_SECTIONS = {
    "personal_info": {
        "title": "Personal Information",
        "fields": {
            "first_name": {
                "question": "What is your first name?",
                "type": "text",
                "required": True,
                "validation": lambda x: len(x.strip()) > 0
            },
            "last_name": {
                "question": "What is your last name?",
                "type": "text", 
                "required": True,
                "validation": lambda x: len(x.strip()) > 0
            },
            "age": {
                "question": "What is your age?",
                "type": "number",
                "required": True,
                "validation": lambda x: x.isdigit() and 0 <= int(x) <= 120
            },
            "date_of_birth": {
                "question": "What is your date of birth? (YYYY-MM-DD)",
                "type": "date",
                "required": True,
                "validation": lambda x: len(x) == 10 and x.count('-') == 2
            }
        }
    },
    "contact_details": {
        "title": "Contact Details",
        "fields": {
            "email": {
                "question": "What is your email address?",
                "type": "email",
                "required": True,
                "validation": lambda x: "@" in x and "." in x.split("@")[-1]
            },
            "phone": {
                "question": "What is your phone number?",
                "type": "phone",
                "required": True,
                "validation": lambda x: len(x.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")) >= 10
            },
            "address": {
                "question": "What is your street address?",
                "type": "text",
                "required": True,
                "validation": lambda x: len(x.strip()) > 5
            },
            "city": {
                "question": "What city do you live in?",
                "type": "text",
                "required": True,
                "validation": lambda x: len(x.strip()) > 0
            },
            "postal_code": {
                "question": "What is your postal/zip code?",
                "type": "text",
                "required": True,
                "validation": lambda x: len(x.strip()) >= 5
            }
        }
    },
    "preferences": {
        "title": "Preferences & Settings",
        "fields": {
            "newsletter": {
                "question": "Would you like to receive our newsletter? (yes/no)",
                "type": "boolean",
                "required": True,
                "validation": lambda x: x.lower() in ["yes", "no", "y", "n"]
            },
            "communication_method": {
                "question": "Preferred communication method? (email/phone/mail)",
                "type": "choice",
                "required": True,
                "validation": lambda x: x.lower() in ["email", "phone", "mail"]
            },
            "interests": {
                "question": "What are your main interests? (comma-separated)",
                "type": "text",
                "required": False,
                "validation": lambda x: True  # Optional field, always valid
            }
        }
    }
}


def form_handler(state: FormState) -> FormState:
    """
    Main form handler node that presents questions and collects user input.
    Uses interrupt() to pause execution and wait for user input.
    """
    section_names = list(FORM_SECTIONS.keys())
    current_section_name = section_names[state["current_section"]]
    current_section = FORM_SECTIONS[current_section_name]
    
    # Get fields for current section
    fields = current_section["fields"]
    field_names = list(fields.keys())
    
    # Process each field in the current section
    for field_name in field_names:
        field_config = fields[field_name]
        
        # Skip if already answered
        if field_name in state.get("responses", {}):
            continue
            
        # Prepare question prompt
        question = field_config["question"]
        required_text = " (required)" if field_config["required"] else " (optional)"
        prompt = f"\n=== {current_section['title']} ===\n{question}{required_text}\n"
        
        # Use interrupt to pause and collect user input
        user_response = interrupt({
            "section": current_section_name,
            "field": field_name,
            "question": prompt,
            "type": field_config["type"],
            "required": field_config["required"]
        })
        
        # Store the response and current field info for validation
        updated_responses = state.get("responses", {}).copy()
        updated_responses[field_name] = user_response
        
        return {
            "responses": updated_responses,
            "current_field": field_name,
            "current_question": question,
            "validation_errors": []
        }
    
    # All fields in section completed, move to next section
    return {
        "current_section": state["current_section"] + 1,
        "current_field": None,
        "current_question": None
    }


def validation_handler(state: FormState) -> FormState:
    """
    Validates user responses according to field validation rules.
    """
    if not state.get("current_field"):
        return {"validation_errors": []}
    
    field_name = state["current_field"]
    user_response = state["responses"].get(field_name, "")
    
    # Find the field configuration
    section_names = list(FORM_SECTIONS.keys())
    current_section_name = section_names[state["current_section"]]
    field_config = FORM_SECTIONS[current_section_name]["fields"][field_name]
    
    validation_errors = []
    
    # Check if required field is empty
    if field_config["required"] and not user_response.strip():
        validation_errors.append(f"Field '{field_name}' is required and cannot be empty.")
    
    # Run field-specific validation if response is not empty
    if user_response.strip():
        try:
            if not field_config["validation"](user_response):
                validation_errors.append(f"Invalid format for field '{field_name}'. Please check your input.")
        except Exception as e:
            validation_errors.append(f"Validation error for field '{field_name}': {str(e)}")
    
    return {"validation_errors": validation_errors}


def completion_handler(state: FormState) -> FormState:
    """
    Handles final form processing and completion.
    """
    # Generate form summary
    summary_data = {
        "total_responses": len(state.get("responses", {})),
        "sections_completed": state["current_section"],
        "responses": state.get("responses", {})
    }
    
    # Use interrupt to show final summary and get confirmation
    confirmation = interrupt({
        "type": "completion",
        "message": "Form completed! Here's your summary:",
        "summary": summary_data,
        "question": "Is this information correct? (yes/no)"
    })
    
    if confirmation.lower() in ["yes", "y"]:
        return {"is_complete": True}
    else:
        # Reset to first section to allow corrections
        return {
            "current_section": 0,
            "is_complete": False,
            "validation_errors": ["Form reset for corrections."]
        }


def should_validate(state: FormState) -> Literal["validation_handler", "form_handler"]:
    """
    Conditional edge function to determine if validation is needed.
    """
    if state.get("current_field") and state.get("responses", {}).get(state["current_field"]):
        return "validation_handler"
    return "form_handler"


def should_continue_form(state: FormState) -> Literal["form_handler", "completion_handler", END]:
    """
    Conditional edge function to determine next step in form flow.
    """
    # Check for validation errors - stay in form if errors exist
    if state.get("validation_errors") and len(state["validation_errors"]) > 0:
        return "form_handler"
    
    # Check if form is complete
    if state.get("is_complete", False):
        return END
    
    # Check if all sections are completed
    if state["current_section"] >= state["total_sections"]:
        return "completion_handler"
    
    # Continue with form
    return "form_handler"


# Build the StateGraph
def create_form_agent():
    """Create and return the compiled form-filling agent graph."""
    
    # Initialize the graph builder
    graph_builder = StateGraph(FormState)
    
    # Add nodes
    graph_builder.add_node("form_handler", form_handler)
    graph_builder.add_node("validation_handler", validation_handler)
    graph_builder.add_node("completion_handler", completion_handler)
    
    # Add edges
    graph_builder.add_edge(START, "form_handler")
    
    # Add conditional edges
    graph_builder.add_conditional_edges(
        "form_handler",
        should_validate,
        {
            "validation_handler": "validation_handler",
            "form_handler": "form_handler"
        }
    )
    
    graph_builder.add_conditional_edges(
        "validation_handler", 
        should_continue_form,
        {
            "form_handler": "form_handler",
            "completion_handler": "completion_handler",
            END: END
        }
    )
    
    graph_builder.add_conditional_edges(
        "completion_handler",
        should_continue_form,
        {
            "form_handler": "form_handler",
            END: END
        }
    )
    
    # Compile the graph
    return graph_builder.compile()


# Create the agent and export as 'app' (required for LangGraph deployment)
app = create_form_agent()


# CLI interaction functions
def run_cli_form():
    """
    Run the CLI form-filling interaction loop.
    Handles interrupt/resume cycle for user input collection.
    """
    print("🔥 Welcome to the CLI Form-Filling Agent! 🔥")
    print("This agent will guide you through filling out a multi-section form.")
    print("You can type 'quit' at any time to exit.\n")
    
    # Initialize checkpointer and config
    checkpointer = InMemorySaver()
    graph = create_form_agent().compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "form_session_1"}}
    
    # Initialize form state
    section_names = list(FORM_SECTIONS.keys())
    initial_state = {
        "current_section": 0,
        "total_sections": len(section_names),
        "section_names": section_names,
        "responses": {},
        "is_complete": False,
        "validation_errors": [],
        "current_field": None,
        "current_question": None
    }
    
    try:
        # Start the form-filling process
        result = graph.invoke(initial_state, config=config)
        
        # Handle interrupts in a loop
        while True:
            # Check if we need to handle an interrupt
            state = graph.get_state(config)
            
            if state.next:  # There's an interrupt waiting
                # Get the interrupt data
                interrupt_data = None
                if hasattr(state, 'tasks') and state.tasks:
                    for task in state.tasks:
                        if hasattr(task, 'interrupts') and task.interrupts:
                            interrupt_data = task.interrupts[0].value
                            break
                
                if interrupt_data:
                    if interrupt_data.get("type") == "completion":
                        # Handle completion confirmation
                        print(f"\n{interrupt_data['message']}")
                        print("\n=== FORM SUMMARY ===")
                        for field, value in interrupt_data["summary"]["responses"].items():
                            print(f"{field}: {value}")
                        print(f"\nTotal responses: {interrupt_data['summary']['total_responses']}")
                        print(f"Sections completed: {interrupt_data['summary']['sections_completed']}")
                        
                        user_input = input(f"\n{interrupt_data['question']} ").strip()
                    else:
                        # Handle regular field input
                        print(interrupt_data["question"])
                        user_input = input("Your answer: ").strip()
                    
                    # Check for quit command
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Thanks for using the form agent! Goodbye!")
                        break
                    
                    # Resume execution with user input
                    result = graph.invoke(Command(resume=user_input), config=config)
                    
                    # Check if form is complete
                    current_state = graph.get_state(config)
                    if current_state.values.get("is_complete", False):
                        print("\n🎉 Form completed successfully!")
                        print("Thank you for filling out the form!")
                        break
                        
                    # Show validation errors if any
                    if current_state.values.get("validation_errors"):
                        for error in current_state.values["validation_errors"]:
                            print(f"❌ {error}")
                        print("Please try again.\n")
                else:
                    # No more interrupts, form is complete
                    break
            else:
                # No interrupts, check if complete
                current_state = graph.get_state(config)
                if current_state.values.get("is_complete", False):
                    print("\n🎉 Form completed successfully!")
                    break
                else:
                    print("Form processing completed.")
                    break
                    
    except KeyboardInterrupt:
        print("\n\n👋 Form filling interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please try again.")


if __name__ == "__main__":
    run_cli_form()
