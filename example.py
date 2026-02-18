"""
Example usage of the Business AI Copilot.
"""

from src.main import BusinessCopilot



def main():
    print("Initializing Business AI Copilot...")
    print()
    
    # Initialize
    copilot = BusinessCopilot()
    
    # Example query
    query = "Get the status of Project Phoenix and draft an update email for stakeholders."
    
    print(f"Query: {query}")
    print()
    print("Processing...")
    print()
    
    # Process
    response = copilot.process_query(query)
    
    # Display response
    print("=" * 60)
    print("RESPONSE:")
    print("=" * 60)
    print()
    print(response)
    print()


if __name__ == "__main__":
    main()