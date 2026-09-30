from backend.agent.graph import agent_app

def run():
    initial_state = {
        "user_prompt": "Show me the top 5 regions by revenue.",
        "sql_retries": 0,
        "errors": ""
    }
    
    print("==================================================")
    print(f"Agent Started: '{initial_state['user_prompt']}'")
    print("==================================================\n")
    
    try:
        final_merged_state = initial_state.copy()
        for s in agent_app.stream(initial_state):
            node_name = list(s.keys())[0]
            state_data = s[node_name]
            final_merged_state.update(state_data)

            print(f"-> Finished Node: [{node_name}]")

            if node_name == "lookup_semantics":
                print(f"   Mapped Semantics: Found {len(state_data.get('semantic_mapping', ''))} characters of schema.")
            elif node_name == "generate_sql":
                print(f"   Generated SQL: {state_data.get('generated_sql')}")
            elif node_name == "validate_and_retrieve":
                if state_data.get('sql_validation') != "VALID":
                    print(f"   SQL Error: {state_data.get('sql_validation')} (Retrying...)")
                else:
                    print(f"   Data Retrieved: {len(state_data.get('query_result', []))} rows")
            
        print("\n==================================================")
        print("Agent Finished Successfully!")
        print("==================================================")
        print(f"Suggested Chart: {final_merged_state.get('visualization')}")
        print(f"Insight: {final_merged_state.get('insights')}")
        
        # Save the trace via AgentTrace carried in state
        trace = final_merged_state.get("trace")
        if trace:
            trace_path = trace.save(final_merged_state)
            print(f"\nExecution Trace saved to: {trace_path}")
        
    except Exception as e:
        print(f"\nAgent Failed with exception: {e}")

if __name__ == "__main__":
    run()
