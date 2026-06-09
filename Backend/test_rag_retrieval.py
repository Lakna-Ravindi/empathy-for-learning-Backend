import sys
import os

# Ensure parent directory is in path so app imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables (needed to initialize components)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from app.services.rag_service import RAGService

def test_rag(query: str, skill: str = None):
    print("=" * 80)
    print(f"Query: \"{query}\"")
    if skill:
        print(f"Skill Filter: \"{skill}\"")
    print("=" * 80)
    
    # Initialize RAG Service
    rag_service = RAGService()
    
    # Search the vector database
    results = rag_service.search(query=query, skill=skill, top_k=3)
    
    if not results:
        print("❌ No matching chunks found. Make sure the RAG index is built!")
        return

    # Print matching chunks
    for i, chunk in enumerate(results, 1):
        print(f"\n[Match {i}]")
        print(f"📄 Source PDF: {chunk.get('source_pdf', 'Unknown')}")
        print(f"📖 Page: {chunk.get('page_number', 'Unknown')}")
        print(f"🛠️ Mapped Skill: {chunk.get('skill', 'Unknown')}")
        print(f"📝 Content Preview:")
        print(f"   \"{chunk.get('content', '').strip()[:300]}...\"")
        print("-" * 80)

if __name__ == "__main__":
    # Test queries
    test_rag(query="feeling anxious and overwhelmed", skill="Calming the Body and Mind")
    test_rag(query="I am so angry and had an impulse reaction", skill="Ethical Mindfulness")
