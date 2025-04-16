# Chatbot with Agentic RAG Langgraph

### 1. Introduction 

This document outlines a **LangGraph**-orchestrated RAG chatbot for HDFC Bank, focusing on loan services and FAQs. The system uses **vector retrieval**, **knowledge graphs**, and agentic workflows to resolve queries. 

### 2. **Core Components** 
#### A. ***Data Sources*** 
- **Loan Products**: Eligibility criteria, EMI calculators, terms & conditions. 
- **FAQs**: Preprocessed Q/A pairs (e.g., "How to check loan status?"). 
- **Interest Rates**: Versioned JSON files (daily updates). 
#### B. ***Vector Database Example Row***  
```json
   {   "id": "loan_eligibility_123",   
   "text": "Salaried individuals must provide 3 months' payslips and a credit score above 750.",   
   "metadata": {   
        "category": "loans",   
        "subcategory": "eligibility",   
        "product": "personal loan",   
        "effective_date": "2024-05-01",
        "source_url":"www.hdfc.com/loan",
        "chunk_id" : 6
   },   
   "embedding": [0.23, -0.45, 0.67, ...],
   } 
```
### 3. **LangGraph Agentic Workflow** 
#### A. ***Agent Roles*** 

|**Agent** |**Role** |
| - | - |
|**Router Agent** |Classifies query intent  |
|**Retriever Agent** |Fetches chunks from ChromaDB using hybrid search. |
|**Knowledge Graph Agent** |Queries Neo4j for multi-hop relationships. |
|**Synthesizer Agent** |Generates responses using LLM. |

#### B. ***Workflow Diagram*** 

![](Aspose.Words.80fca639-3e58-4386-b03e-ad9d72845026.001.jpeg)

### 4. **Knowledge Graph Design** 
#### A. ***Graph Schema*** 
- **Nodes**: Loan , Document , InterestRate , FAQ . 
- **Relationships**: 
- Loan -[REQUIRES]-> Document  
- Loan -[HAS\_RATE]-> InterestRate  
- FAQ -[RELATED\_TO]-> Loan  
#### B. ***Example Query*** 

**User Input**: "What documents are needed for a home loan?" 
**Cypher Query**: 
```
MATCH (l:Loan {type: "Home Loan"})-[r:REQUIRES]->(d:Document)   RETURN d.name; 
```
**Result**: 
`["Property papers", "Salary slips", "PAN card"]. `

### 5. **Deployment Architecture** 
1. **API Layer**: FastAPI exposes /query endpoint. 
1. **Vector DB**: ChromaDB hosted on AWS EC2. 
1. **Knowledge Graph**: Neo4j running in Docker. 
1. **Agents**: LangGraph workflows deployed as serverless functions. 

### **6. Example Query Flow** 

**Query**: "What’s the interest rate for a ₹20L personal loan?" 

1. **Router Agent**: Detects intent subcategory(interest\_rate) and product(personal\_loan). 
1. **Retriever Agent**: 
   1. Searches VectorDB for "personal loan" + "interest rate" chunks. 
   1. Filters metadata by effective\_date=2024-05-01. 
1. **Knowledge Graph Agent**: 

a.  Fetches linked nodes: Personal Loan → Interest Rate → 10.5%. 

4. **Synthesizer Agent**: Generates: *"As of May 2024, the interest rate for a ₹20L personal loan is 10.5%."* 

*Architecture:* 

![](Aspose.Words.80fca639-3e58-4386-b03e-ad9d72845026.002.jpeg)
