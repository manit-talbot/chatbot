from crewai_tools import RagTool, NL2SQLTool
from crewai import Agent, Task, Crew, Process
from crewai_tools.aws.bedrock.knowledge_base.retriever_tool import BedrockKBRetrieverTool
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import glob
import logging

load_dotenv()

DB_URI = os.getenv("POSTGRES_URI")
DEFAULT_SCHEMA = os.getenv("DEFAULT_SCHEMA", "public")
DOCS_DIR = os.getenv("DOCS_DIR")
KB_ID = os.getenv("KB_ID")

# Setup logging
def setup_logging():
    """Setup logging configuration"""
    os.makedirs("logs", exist_ok=True)
    log_filename = f"logs/agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Log file: {log_filename}")
    return logger

# Initialize logger
logger = setup_logging()

# Test logging
logger.info("=== AGENT STARTUP ===")
logger.info("Logger initialized successfully")



logger.info(f"Environment loaded - DB_URI: {'Set' if DB_URI else 'Not set'}")
logger.info(f"Default Schema: {DEFAULT_SCHEMA}")
#logger.info(f"Docs Directory: {DOCS_DIR}")

# Database configuration
DATABASE_NAME = "talbotdevv1"
AVAILABLE_TABLES = [
    #"PolicyAuthorizationNumber",
    #"Patient", 
    #"PatientPolicy",
    #"InsurancePolicy",
    #"InsurancePolicyHolder",
    "InsuranceCompany",  
    #"InsuranceCompanyTypes",    
]

# Initialize tools once
logger.info("Initializing RAG tool...")
'''
rag_tool = RagTool()
try:
    if os.path.exists(DOCS_DIR):
        rag_tool.add(data_type="directory", source=DOCS_DIR)
        logger.info(f"Successfully added docs directory: {DOCS_DIR}")
        print("Successfully added docs-text directory to RAG tool")
    else:
        logger.warning(f"Docs directory not found: {DOCS_DIR}")
        print("docs-text directory not found")
except Exception as e:
    logger.error(f"Error adding files to RAG tool: {e}")
    print(f"Error adding files to RAG tool: {e}")
    print("Continuing without RAG data...")
'''
# Test database connection first
def test_database_connection(uri):
    """Test if we can connect to the database"""
    try:
        import psycopg2
        logger.info("Testing database connection...")
        print("Testing database connection...")
        conn = psycopg2.connect(uri)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"Database connection successful - PostgreSQL version: {version[0]}")
        #print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        #print(f"❌ Database connection failed: {e}")
        return False

# Initialize NL2SQL tool
nl2sql_tool = None
if DB_URI:
    print(f"Attempting to initialize NL2SQL tool...")
    print(f"Database URI: {DB_URI}")
    print(f"Default Schema: {DEFAULT_SCHEMA}")
    
    try:
        # Ensure the URI points to the correct database
        if "talbotdevv1" not in DB_URI:
            # Update URI to include the correct database name
            # Replace the database name in the URI
            if DB_URI.endswith("/"):
                DB_URI = DB_URI + "talbotdevv1"
            else:
                DB_URI = DB_URI + "/talbotdevv1"
            print(f"Updated URI to: {DB_URI}")
        
        # Test database connection first
        if test_database_connection(DB_URI):
            print("Creating NL2SQLTool instance...")
            nl2sql_tool = NL2SQLTool(db_uri=DB_URI, default_schema=DEFAULT_SCHEMA)
            print(f"NL2SQL tool initialized successfully for database: {DATABASE_NAME}")
            print(f"Available tables: {', '.join(AVAILABLE_TABLES)}")
        else:
            print("❌ Cannot initialize NL2SQL tool - database connection failed")
            nl2sql_tool = None
    except Exception as e:
        print(f"❌ NL2SQL tool initialization failed: {e}")
        print(f"Error type: {type(e)}")
        print("Continuing without database search functionality...")
        nl2sql_tool = None
else:
    print("❌ No database URI provided - Database search functionality disabled")
    print("Please set POSTGRES_URI in your .env file")

    # Method 2: If directory doesn't work, try adding individual files
    # md_files = glob.glob("docs-text/*.md")
    # for file_path in md_files:
    #     try:
    #         rag_tool.add(data_type="file", source=file_path)
    #         print(f"Added {file_path} to RAG tool")
    #     except Exception as e:
    #         print(f"Failed to add {file_path}: {e}")


# Initialize the tool
kb_tool = BedrockKBRetrieverTool(
    knowledge_base_id=KB_ID,
    number_of_results=5
)
'''
# Create Knowledge Expert Agent
def create_knowledge_agent():
    try:
        logger.info("Creating Knowledge Expert Agent...")
        agent = Agent(
           role='Knowledge Expert',
           goal='Answer questions using the provided knowledge base from markdown files',
           backstory="""
            You are an expert knowledge assistant with access to a comprehensive knowledge base
            stored in markdown files. You excel at finding relevant information, synthesizing
            content from multiple sources, and providing clear, accurate answers to user questions.
            Always use the RAG tool to search through the knowledge base before answering.
            """,
            verbose=False,
            allow_delegation=False,
            tools=[rag_tool],
            llm_config={
               "temperature": 0.1,
            }
        )
        logger.info("Knowledge Expert Agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating knowledge agent: {e}")
        print(f"Error creating knowledge agent: {e}")
        return None
'''
# Create SQL Assistant Agent
def create_sql_agent():
    if nl2sql_tool is None:
        logger.warning("SQL agent not created - NL2SQL tool not available")
        print("Warning: SQL agent not created - NL2SQL tool not available")
        return None
    
    try:
        logger.info("Creating SQL Assistant Agent with NL2SQL tool...")
        print("Creating SQL agent with NL2SQL tool...")
        agent = Agent(
            role="SQL Assistant", 
            goal="Answer questions by querying the database using natural language to SQL conversion",
            backstory=f"""
            You are a SQL assistant that translates natural language questions into SQL queries 
            and executes them safely against the talbotdevv1 database. You have access to these tables:
            {', '.join(AVAILABLE_TABLES)}. You only perform SELECT queries and never modify data. 
            Always provide clear explanations of your results and cite which tables you used.
            """,
            tools=[nl2sql_tool],
            verbose=False,
            allow_delegation=False,
            llm_config={
                "temperature": 0.0,
            }
        )
        logger.info("SQL Assistant Agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating SQL agent: {e}")
        print(f"Error creating SQL agent: {e}")
        return None

def create_kb_agent():
    try:
        logger.info("Creating Knowledge Base Agent...")
        agent = Agent(
            role="Knowledge Base Agent",
            goal="Answer questions using the provided knowledge base from markdown files",
            backstory="""
            You are an expert knowledge assistant with access to a comprehensive knowledge base
            stored in markdown files. You excel at finding relevant information, synthesizing
            content from multiple sources, and providing clear, accurate answers to user questions.
            Always use the RAG tool to search through the knowledge base before answering.
            """,
            tools=[kb_tool],
            verbose=False,
            allow_delegation=False,
            llm_config={
                "temperature": 0.1,
            }
        )
        logger.info("Knowledge Base Agent created successfully")
        return agent
    except Exception as e:
        logger.error(f"Error creating Knowledge Base agent: {e}")
        print(f"Error creating Knowledge Base agent: {e}")
        return None
'''
# Create Knowledge Task
def create_knowledge_task(user_question: str, conversation_history: list = None, agent=None):
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
        agent=agent
    )
'''
# Create SQL Task
def create_sql_task(user_question: str, conversation_history: list = None, agent=None):
    context = ""
    if conversation_history and len(conversation_history) > 0:
        context = "\n\nPrevious conversation context:\n"
        # Include last 3 exchanges for context
        recent_history = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        for exchange in recent_history:
            context += f"User: {exchange['user']}\nAI: {exchange['ai'][:200]}...\n\n"
    return Task(
        description=f"""
        Answer this question by querying the database using SQL.
        
        User Question: "{user_question}"
        {context}

        Instructions:
        1. Use the NL2SQL tool to convert the natural language question to SQL
        2. Query only these tables: {', '.join(AVAILABLE_TABLES)}
        3. Execute the SQL query safely (SELECT only, no modifications)
        4. Provide a clear answer based on the query results
        5. If no relevant data exists, explain what was searched for
        6. Be helpful and conversational in your response
        """,
        expected_output="A clear answer based on database query results",
        agent=agent
    )

def create_kb_task(user_question: str, conversation_history: list = None, agent=None):
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
        1. Use the RAG tool to search through the knowledge base for relevant information
        2. Provide a comprehensive answer based on the found information
        3. If you find relevant information, cite or reference the source when possible
        4. If the information is not available in the knowledge base, clearly state that
        5. Be conversational and helpful in your response
        6. Consider the conversation history to provide contextual answers
        """,
        expected_output="A detailed, helpful answer to the user's question based on information found in the knowledge base.",
        agent=agent
    )

# Main conversational loop
def run_knowledge_assistant():
    print("\n===== KNOWLEDGE BASE ASSISTANT =====")
    print("Ask me anything about your documents or database.")
    print("Type 'exit' to quit.\n")

    os.makedirs("conversation_history", exist_ok=True)
    conversation_history = []
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    while True:
        user_question = input("\nYou: ")

        if user_question.lower() in ['exit', 'quit', 'bye']:
            print("\nThank you for using the Knowledge Base Assistant. Goodbye!")
            break

        print("\nProcessing your question...")
        logger.info(f"Processing user question: {user_question}")

        try:
            # Prepare agents and tasks (only include valid agents)
            agents = []
            tasks = []
            '''
            # Add knowledge agent (always available)
            logger.info("Creating Knowledge Agent...")
            knowledge_agent = create_knowledge_agent()
            if knowledge_agent is not None:
                agents.append(knowledge_agent)
                knowledge_task = create_knowledge_task(user_question, conversation_history, knowledge_agent)
                tasks.append(knowledge_task)
                logger.info("Knowledge agent ready and added to crew")
                print(f"Knowledge agent ready")
            else:
                logger.error("Knowledge agent failed to create")
                print("Knowledge agent failed to create")
            '''
            # Add SQL agent (only if available)
            logger.info("Creating SQL Agent...")
            sql_agent = create_sql_agent()
            if sql_agent is not None:
                agents.append(sql_agent)
                sql_task = create_sql_task(user_question, conversation_history, sql_agent)
                tasks.append(sql_task)
                logger.info("SQL agent ready and added to crew")
                print(f"SQL agent ready")
            else:
                logger.warning("SQL agent not available")
                print("SQL agent not available")
            
            # Add Knowledge Base Agent (always available)
            logger.info("Creating Knowledge Base Agent...")
            kb_agent = create_kb_agent()
            if kb_agent is not None:
                agents.append(kb_agent)
                kb_task = create_kb_task(user_question, conversation_history, kb_agent)
                tasks.append(kb_task)
                logger.info("Knowledge Base agent (aws kb) ready and added to crew")
                print(f"Knowledge Base agent ready")
            else:
                logger.error("Knowledge Base agent not available")
                print("Knowledge Base agent not available")
            
            # Ensure we have at least one agent
            if not agents:
                logger.error("No agents available")
                result_str = "Error: No agents available. Please check your configuration."
            elif len(agents) != len(tasks):
                logger.error(f"Mismatch between agents ({len(agents)}) and tasks ({len(tasks)}) count")
                result_str = "Error: Mismatch between agents and tasks count."
            else:
                logger.info(f"Running crew with {len(agents)} agent(s)...")
                print(f"Running crew with {len(agents)} agent(s)...")
                
                # Log which agents are running
                for i, agent in enumerate(agents):
                    logger.info(f"Agent {i+1}: {agent.role}")
                
                # Run crew
                crew = Crew(
                    agents=agents,
                    tasks=tasks,
                    verbose=False,
                    process=Process.sequential
                )

                logger.info("Starting crew execution...")
                crew_output = crew.kickoff()
                logger.info("Crew execution completed")
                
                if hasattr(crew_output, 'raw_output'):
                    result_str = crew_output.raw_output
                    logger.info("Using raw_output from crew result")
                elif hasattr(crew_output, 'result'):
                    result_str = crew_output.result
                    logger.info("Using result from crew output")
                else:
                    result_str = str(crew_output)
                    logger.info("Using string representation of crew output")

        except Exception as e:
            result_str = f"Error processing your question: {str(e)}"

        print(f"\nAI: {result_str}")
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

# Test function to debug NL2SQL tool
def test_nl2sql_tool():
    """Test the NL2SQL tool directly"""
    if nl2sql_tool is None:
        print("NL2SQL tool is not available")
        return
    
    print("Testing NL2SQL tool...")
    try:
        # Test with a simple query on one of your tables
        result = nl2sql_tool.run("How many patients are in the Patient table?")
        print(f"Test result: {result}")
    except Exception as e:
        print(f"NL2SQL tool test failed: {e}")
        print(f"Error type: {type(e)}")
        print("This is expected if the tool has parameter validation issues")

# Main execution
if __name__ == "__main__":
    # Uncomment the next line to test the NL2SQL tool
    #test_nl2sql_tool()
    run_knowledge_assistant()