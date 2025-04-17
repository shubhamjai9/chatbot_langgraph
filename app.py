import gradio as gr
from final_chatbot import main, app  # Import your compiled LangGraph workflow


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


def respond(message, chat_history, agent_state):
    """Process user message through the agent workflow"""
    try:
        # Update state with new query
        agent_state["user_query"] = message

        # Process through workflow
        final_state = None
        for output in app.stream(agent_state):
            for key, state in output.items():
                final_state = state
                print(f"Node: {key}")
                print(f"State: {value}\n")

        if final_state and final_state.get("llm_response"):
            bot_response = final_state["llm_response"]
        else:
            bot_response = "Sorry, I couldn't process that request."

        chat_history.append((message, bot_response))
        return "", chat_history, final_state

    except Exception as e:
        print(f"Error: {str(e)}")
        chat_history.append(
            (message, "Sorry, I'm experiencing technical difficulties.")
        )
        return "", chat_history, agent_state


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# HDFC Loan Chatbot 💬🏦")

    with gr.Row():
        chatbot = gr.Chatbot(height=500)
        with gr.Column():
            gr.Markdown("### Loan Assistance Features:")
            gr.Markdown(
                "- Loan eligibility checks\n- Document requirements\n- Product comparisons\n- Payment calculations"
            )
            gr.Markdown("---")
            gr.Markdown(
                "**Note**: All responses are AI-generated\nand should be verified with official documents"
            )

    msg = gr.Textbox(
        label="Type your loan-related question:", placeholder="Ask about loans..."
    )
    agent_state = gr.State(initialize_state)

    with gr.Row():
        submit_btn = gr.Button("Submit", variant="primary")
        clear_btn = gr.Button("Clear Chat")

    msg.submit(respond, [msg, chatbot, agent_state], [msg, chatbot, agent_state])
    submit_btn.click(respond, [msg, chatbot, agent_state], [msg, chatbot, agent_state])

    clear_btn.click(
        lambda: ([], initialize_state()),
        outputs=[chatbot, agent_state],
        show_progress=False,
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
