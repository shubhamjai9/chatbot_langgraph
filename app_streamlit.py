import streamlit as st
from final_chatbot import main, app  # Import your compiled LangGraph workflow

# Page configuration
st.set_page_config(page_title="HDFC Loan Chatbot 💬🏦", page_icon="🏦", layout="wide")


# Initialize session state
def initialize_state():
    """Create initial agent state"""
    return {
        "user_query": "",
        "auth_status": False,
        "route_decision": None,
        "rag_results": None,
        "graph_results": None,
        "api_results": None,
        "llm_response": None,
        "guardrail_approved": False,
    }


if "agent_state" not in st.session_state:
    st.session_state.agent_state = initialize_state()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Processing function
def process_message(message):
    """Process user message through the agent workflow"""
    try:
        # Update state with new query
        st.session_state.agent_state["user_query"] = message

        # Process through workflow
        final_state = None
        for output in app.stream(st.session_state.agent_state):
            for key, state in output.items():
                final_state = state
                print(f"Node: {key}")
                print(f"State: {state}\n")

        if final_state and final_state.get("llm_response"):
            bot_response = final_state["llm_response"]
        else:
            bot_response = "Sorry, I couldn't process that request."

        # Update chat history
        st.session_state.chat_history.append(("user", message))
        st.session_state.chat_history.append(("assistant", bot_response))
        st.session_state.agent_state = final_state or st.session_state.agent_state

    except Exception as e:
        print(f"Error: {str(e)}")
        st.session_state.chat_history.append(
            ("assistant", "Sorry, I'm experiencing technical difficulties.")
        )


# UI Layout
st.title("HDFC Loan Chatbot 💬🏦")

col1, col2 = st.columns([3, 1])

with col1:
    # Chat container
    chat_container = st.container(height=500)

    # Display chat messages
    for role, message in st.session_state.chat_history:
        with chat_container.chat_message(role):
            st.markdown(message)

with col2:
    st.markdown("### Loan Assistance Features:")
    st.markdown(
        "- Loan eligibility checks\n- Document requirements\n- Product comparisons\n- Payment calculations"
    )
    st.markdown("---")
    st.markdown(
        "**Note**: All responses are AI-generated\nand should be verified with official documents"
    )

    # Clear button
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.agent_state = initialize_state()
        st.rerun()

# Chat input
user_input = st.chat_input("Type your loan-related question:", key="input")

if user_input:
    process_message(user_input)
    st.rerun()
