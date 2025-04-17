from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.graphs import Neo4jGraph
from langgraph.graph import END, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import TypedDict, List, Dict, Optional


# Define State Schema
class AgentState(TypedDict):
    user_query: str
    auth_status: bool
    route_decision: Optional[str]
    rag_results: Optional[List[Dict]]
    graph_results: Optional[List[Dict]]
    api_results: Optional[Dict]
    llm_response: Optional[str]
    guardrail_approved: bool


# Initialize Components
llm = ChatOpenAI(model="gpt-3.5-turbo")
CHROMA_PATH = "./database"
vectorstore = Chroma(
    persist_directory=f"{CHROMA_PATH}/openai",
    collection_name="test",
    embedding_function=OpenAIEmbeddings(),
)
# neo4j_graph = Neo4jGraph(
#     url="bolt://localhost:7687", username="neo4j", password="password"
# )


# Define Nodes
def master_agent(state: AgentState) -> AgentState:
    """Initial entry point for all queries"""
    state["auth_status"] = True  # Add real authentication logic
    return state


def router_agent(state: AgentState) -> AgentState:
    """Enhanced router with proper LangChain routing"""
    # Create classification prompt
    prompt = ChatPromptTemplate.from_template(
        """
    Classify the following banking query into one of these categories:
    - FAQ: General questions about loans, policies, or procedures
    - LoanDependency: Questions about loan relationships, requirements, or dependencies
    - Transaction: Queries requiring API calls (payments, eligibility checks)
    
    Query: {query}
    
    Respond ONLY with one of the specified categories.
    """
    )

    # Create classification chain
    classification_chain = prompt | llm | StrOutputParser()

    # Get classification
    category = classification_chain.invoke({"query": state["user_query"]})

    # Clean and validate response
    category = category.strip().lower()
    if "faq" in category:
        state["route_decision"] = "FAQ"
    elif "dependency" in category:
        state["route_decision"] = "FAQ"  # "LoanDependency"
    elif "transaction" in category:
        state["route_decision"] = "Transaction"
    else:
        state["route_decision"] = "FAQ"  # Default fallback

    return state


def rag_agent(state: AgentState) -> AgentState:
    """Handle FAQ queries using vector DB"""
    # retriever = vectorstore.as_retriever()
    # docs = retriever.get_relevant_documents(state["user_query"])
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 1,
            "fetch_k": 10,
            "lambda_mult": 0.5,
            "score_threshold": 0.5,
        },
    )
    docs = retriever.invoke(state["user_query"])

    state["rag_results"] = [{"content": doc.page_content} for doc in docs]
    return state


def graphrag_agent(state: AgentState) -> AgentState:
    pass


def external_tools_agent(state: AgentState) -> AgentState:
    """Handle external API calls"""
    state["api_results"] = {"status": "simulated", "data": "API response"}
    return state


def conversational_agent(state: AgentState) -> AgentState:
    """Generate final response with LLM"""
    context = []
    if state.get("rag_results"):
        context.append(
            "FAQ Context:\n" + "\n".join([r["content"] for r in state["rag_results"]])
        )
    # if state.get("graph_results"):
    #     context.append
    if state.get("api_results"):
        context.append(f"API Data: {state['api_results']['data']}")

    response = llm.invoke(
        f"""**User Query**: {state["user_query"]}
        
        **Context**:
        {context if context else 'No relevant context found'}
        
        Provide a helpful, accurate response in bank's official tone."""
    )
    state["llm_response"] = response.content
    return state


def guardrail_agent(state: AgentState) -> AgentState:
    """Validate response safety"""
    state["guardrail_approved"] = True  # Add real guardrail checks
    return state


# Build Workflow with LangGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("master", master_agent)
workflow.add_node("router", router_agent)
workflow.add_node("rag", rag_agent)
# workflow.add_node("graphrag", graphrag_agent)
workflow.add_node("external_tools", external_tools_agent)
workflow.add_node("conversational", conversational_agent)
workflow.add_node("guardrail", guardrail_agent)

# Set Entry Point
workflow.set_entry_point("master")

# Define Edges
workflow.add_edge("master", "router")

# Conditional Routing
workflow.add_conditional_edges(
    "router",
    lambda state: state["route_decision"],
    {"FAQ": "rag", "Transaction": "external_tools"},
)  # "LoanDependency": "graphrag",

# Common processing path
workflow.add_edge("rag", "conversational")
# workflow.add_edge("graphrag", "conversational")
workflow.add_edge("external_tools", "conversational")
workflow.add_edge("conversational", "guardrail")

# Guardrail handling
workflow.add_conditional_edges(
    "guardrail", lambda state: END if state["guardrail_approved"] else "conversational"
)

# Compile the workflow
app = workflow.compile()


def main(user_query):
    inputs = {"user_query": user_query}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Node: {key}")
            print(f"State: {value}\n")
    try:
        print("Final Chat Response: \n", output["guardrail"]["llm_response"])
        return output["guardrail"]["llm_response"]
    except Exception as e:
        print("no key llm_response", str(e))


# Example Usage
if __name__ == "__main__":
    main("What documents needed for home loan?")
