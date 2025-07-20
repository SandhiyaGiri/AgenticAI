from googlesearch import search

def google_agent(query, num_results=1):
    results = []
    for url in search(query, num_results=num_results):
        results.append(url)
    return results

# Example usage:
query = "What is Agentic AI?"
top_result = google_agent(query)
print("Top Google result:", top_result[0])
