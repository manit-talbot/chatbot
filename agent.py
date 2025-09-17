from crewai_tools import RagTool
from crewai import Agent, Task, Crew, Process
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import glob

load_dotenv()

# Initialize the RAG tool
rag_tool = RagTool()

# Add all markdown files from your folder
try:
    # Method 1: Try adding as directory first
    if os.path.exists("docs-text"):
        rag_tool.add(data_type="directory", source="docs-text")
        print("Successfully added docs-text directory to RAG tool")
    else:
        print("docs-text directory not found")

    # Method 2: If directory doesn't work, try adding individual files
    # md_files = glob.glob("docs-text/*.md")
    # for file_path in md_files:
    #     try:
    #         rag_tool.add(data_type="file", source=file_path)
    #         print(f"Added {file_path} to RAG tool")
    #     except Exception as e:
    #         print(f"Failed to add {file_path}: {e}")

except Exception as e:
    print(f"Error adding files to RAG tool: {e}")
    print("Continuing without RAG data...")

# Create Knowledge Expert Agent
def create_knowledge_agent():
    return Agent(
        role='Knowledge Expert',
        goal='Answer questions using the provided knowledge base from markdown files',
        backstory="""
        You are an expert knowledge assistant with access to a comprehensive knowledge base
        stored in markdown files. You excel at finding relevant information, synthesizing
        content from multiple sources, and providing clear, accurate answers to user questions.
        Always use the RAG tool to search through the knowledge base before answering.
        """,
        verbose=True,
        allow_delegation=False,
        tools=[rag_tool],
        llm_config={
            "temperature": 0.1,
        }
    )

# Create task for each user question
def create_knowledge_task(user_question: str, conversation_history: list = None) -> Task:
    # Add conversation context if available
    context = ""
    if conversation_history and len(conversation_history) > 0:
        context = "\n\nPrevious conversation context:\n"
        # Include last 3 exchanges for context
        recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        for exchange in recent_history:
            context += f"User: {exchange['user']}\nAI: {exchange['ai'][:200]}...\n\n"

    return Task(
        description=f"""
        Answer the user's question using the knowledge base available through the RAG tool.

        User Question: "{user_question}"
        {context}

        Instructions:
        1. Use the RAG tool to search through the markdown files for relevant information
        2. Provide a comprehensive answer based on the found information
        3. If you find relevant information, cite or reference the source when possible
        4. If the information is not available in the knowledge base, clearly state that
        5. Be conversational and helpful in your response
        6. Consider the conversation history to provide contextual answers
        """,
        expected_output="""
        A detailed, helpful answer to the user's question based on information found in the
        knowledge base. The response should be well-structured, accurate, and cite sources
        when relevant information is found.
        """,
        agent=create_knowledge_agent()
    )

# Main conversational loop
def run_knowledge_assistant():
    print("\n===== KNOWLEDGE BASE ASSISTANT =====")
    print("Ask me anything about the content in your markdown files.")
    print("Type 'exit' to end the conversation.\n")

    # Create conversation history folder
    os.makedirs("conversation_history", exist_ok=True)

    conversation_history = []
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    while True:
        # Get user input
        user_question = input("\nYou: ")

        # Check for exit command
        if user_question.lower() in ['exit', 'quit', 'bye']:
            print("\nThank you for using the Knowledge Base Assistant. Goodbye!")
            break

        print("\nProcessing your question...")

        try:
            # Create a new task for this question
            knowledge_task = create_knowledge_task(user_question, conversation_history)

            # Create and run the crew
            crew = Crew(
                agents=[create_knowledge_agent()],
                tasks=[knowledge_task],
                verbose=False,  # Set to True if you want to see detailed logs
                process=Process.sequential,
            )

            # Execute the task
            crew_output = crew.kickoff()

            # Extract the result
            if hasattr(crew_output, 'raw_output'):
                result_str = crew_output.raw_output
            elif hasattr(crew_output, 'result'):
                result_str = crew_output.result
            else:
                result_str = str(crew_output)

        except Exception as e:
            result_str = f"Error processing your question: {str(e)}"

        # Print the result
        print("\nAI:", result_str)

        # Save to conversation history
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_question,
            "ai": result_str
        }
        conversation_history.append(exchange)

        # Save conversation to file
        history_file = f"conversation_history/knowledge_session_{session_id}.json"
        with open(history_file, 'w') as f:
            json.dump(conversation_history, f, indent=2)

        print("\n" + "-" * 50)

# Main execution
if __name__ == "__main__":
    run_knowledge_assistant()