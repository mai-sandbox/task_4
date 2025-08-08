import json
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
import os


class FormSection(TypedDict):
    name: str
    fields: List[Dict[str, Any]]
    completed: bool
    data: Dict[str, Any]


class FormState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_section: Optional[str]
    sections: List[FormSection]
    form_data: Dict[str, Any]
    completed_sections: List[str]
    all_complete: bool


def initialize_form() -> List[FormSection]:
    """Initialize the form with predefined sections"""
    return [
        {
            "name": "Personal Information",
            "fields": [
                {"name": "first_name", "type": "text", "prompt": "What is your first name?"},
                {"name": "last_name", "type": "text", "prompt": "What is your last name?"},
                {"name": "email", "type": "email", "prompt": "What is your email address?"},
                {"name": "phone", "type": "phone", "prompt": "What is your phone number?"}
            ],
            "completed": False,
            "data": {}
        },
        {
            "name": "Address",
            "fields": [
                {"name": "street", "type": "text", "prompt": "What is your street address?"},
                {"name": "city", "type": "text", "prompt": "What city do you live in?"},
                {"name": "state", "type": "text", "prompt": "What state/province do you live in?"},
                {"name": "zip_code", "type": "text", "prompt": "What is your ZIP/postal code?"}
            ],
            "completed": False,
            "data": {}
        },
        {
            "name": "Additional Information",
            "fields": [
                {"name": "occupation", "type": "text", "prompt": "What is your occupation?"},
                {"name": "comments", "type": "text", "prompt": "Any additional comments or notes?"}
            ],
            "completed": False,
            "data": {}
        }
    ]


def section_selector(state: FormState) -> FormState:
    """Select the next section to fill out"""
    incomplete_sections = [s for s in state["sections"] if not s["completed"]]
    
    if not incomplete_sections:
        state["all_complete"] = True
        state["current_section"] = None
        message = AIMessage(content="✅ All sections have been completed! Here's your form summary:")
        state["messages"].append(message)
    else:
        next_section = incomplete_sections[0]
        state["current_section"] = next_section["name"]
        message = AIMessage(content=f"\n📋 Section: {next_section['name']}\n{'='*40}")
        state["messages"].append(message)
    
    return state


def field_collector(state: FormState) -> FormState:
    """Collect data for fields in the current section"""
    if not state["current_section"]:
        return state
    
    current_section = next(s for s in state["sections"] if s["name"] == state["current_section"])
    
    print(f"\nFilling out: {current_section['name']}")
    print("-" * 40)
    
    section_data = {}
    for field in current_section["fields"]:
        while True:
            user_input = input(f"{field['prompt']}: ").strip()
            
            if not user_input:
                print("⚠️  This field is required. Please provide a value.")
                continue
                
            if field["type"] == "email" and "@" not in user_input:
                print("⚠️  Please enter a valid email address.")
                continue
                
            section_data[field["name"]] = user_input
            break
    
    for section in state["sections"]:
        if section["name"] == state["current_section"]:
            section["data"] = section_data
            section["completed"] = True
            state["form_data"].update(section_data)
            break
    
    state["completed_sections"].append(state["current_section"])
    
    confirmation = input("\n✅ Section completed! Press Enter to continue to the next section...")
    
    return state


def form_summarizer(state: FormState) -> FormState:
    """Summarize the completed form"""
    if not state["all_complete"]:
        return state
    
    print("\n" + "="*50)
    print("FORM SUMMARY")
    print("="*50)
    
    for section in state["sections"]:
        print(f"\n📌 {section['name']}:")
        print("-" * 30)
        for field_name, field_value in section["data"].items():
            display_name = field_name.replace("_", " ").title()
            print(f"  • {display_name}: {field_value}")
    
    print("\n" + "="*50)
    
    save_choice = input("\n💾 Would you like to save this form data? (yes/no): ").strip().lower()
    if save_choice == "yes":
        filename = input("Enter filename (without extension): ").strip()
        if not filename:
            filename = "form_data"
        
        with open(f"{filename}.json", "w") as f:
            json.dump(state["form_data"], f, indent=2)
        print(f"✅ Form data saved to {filename}.json")
    
    message = AIMessage(content="Thank you for completing the form!")
    state["messages"].append(message)
    
    return state


def route_next_step(state: FormState) -> str:
    """Determine the next step in the workflow"""
    if state["all_complete"]:
        return "summarize"
    elif state["current_section"]:
        return "collect_fields"
    else:
        return "select_section"


def create_form_agent():
    """Create the LangGraph agent for form filling"""
    workflow = StateGraph(FormState)
    
    workflow.add_node("select_section", section_selector)
    workflow.add_node("collect_fields", field_collector)
    workflow.add_node("summarize", form_summarizer)
    
    workflow.set_entry_point("select_section")
    
    workflow.add_conditional_edges(
        "select_section",
        route_next_step,
        {
            "collect_fields": "collect_fields",
            "summarize": "summarize"
        }
    )
    
    workflow.add_conditional_edges(
        "collect_fields",
        lambda x: "select_section",
        {
            "select_section": "select_section"
        }
    )
    
    workflow.add_edge("summarize", END)
    
    return workflow.compile()


app = create_form_agent()


if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎯 INTERACTIVE FORM ASSISTANT")
    print("="*50)
    print("Welcome! I'll help you fill out this form step by step.")
    print("Let's begin with the first section.\n")
    
    initial_state = {
        "messages": [],
        "current_section": None,
        "sections": initialize_form(),
        "form_data": {},
        "completed_sections": [],
        "all_complete": False
    }
    
    try:
        result = app.invoke(initial_state)
        print("\n👋 Thank you for using the Form Assistant!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Form filling interrupted by user.")
        print("Your progress has not been saved.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")