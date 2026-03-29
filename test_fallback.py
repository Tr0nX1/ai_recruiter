import os
import sys

# Configure mock API key to instantly cause LLM API failures, isolating the test to fallback traversal
os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-fake-mock-key-for-test"

from crew import build_crew, isolate_agent_fallbacks
from crewai import Task

def test_fallback_logic():
    print("Building crew...")
    crew = build_crew()
    
    # Normally called inside _kickoff_with_retry
    isolate_agent_fallbacks(crew)
    
    # Pick the first agent (Ingestion Agent -> FAST_MODELS)
    agent = crew.agents[0]
    print(f"\n--- Testing Agent: {agent.role} ---")
    
    # Create a dummy task
    dummy_task = Task(description="Parse this mock document", expected_output="Parsed text")
    
    # Execute the wrapped method. Since the API key is fake, every model should fail,
    # trigger the structured logging, and finally safely return the JSON error string.
    try:
         result = agent.execute_task(dummy_task)
         print("\n--- FINAL CONTROLLED RESULT ---")
         print(result)
    except Exception as e:
         print(f"\n--- UNEXPECTED SYSTEM CRASH ---")
         print(e)
         sys.exit(1)

if __name__ == "__main__":
    test_fallback_logic()
