import os
import PyPDF2
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class SimplePDFRAG:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

        # load embedding model
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.chunks = []
        self.embeddings = []

    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file"""
        text = ""
        with open(pdf_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text

    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Split text into overlapping chunks"""
        # clean up text
        text = re.sub(r"\s+", " ", text).strip()

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind(".")
                if last_period > chunk_size * 0.5:
                    end = start + last_period + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

    def load_pdf(self, pdf_path):
        """Load and process PDF"""
        print(f"Loading PDF: {pdf_path}")

        text = self.extract_text_from_pdf(pdf_path)

        # create chunks
        self.chunks = self.chunk_text(text)
        print(f"Created {len(self.chunks)} chunks")

        # generate embeddings
        self.embeddings = self.embedder.encode(self.chunks)
        print("Generated embeddings")

    def retrieve_relevant_chunks(self, query, top_k=3):
        """Retrieve most relevant chunks for query"""
        query_embedding = self.embedder.encode([query])

        # calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        # get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        relevant_chunks = [self.chunks[i] for i in top_indices]
        return relevant_chunks

    def chat(self, question):
        """Chat with the PDF content using Gemini"""
        if not self.chunks:
            return "No PDF loaded. Please load a PDF first."

        # retrieve relevant context
        relevant_chunks = self.retrieve_relevant_chunks(question)
        context = "\n\n".join(relevant_chunks)

        # create prompt
        prompt = f"""Based on the following context from a PDF document, answer the question.

Context:
{context}

Question: {question}

Answer based only on the provided context. If the answer is not in the context, say "I cannot find this information in the provided document."
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"


def main():
    rag = SimplePDFRAG()

    pdf_path = "document.pdf"
    rag.load_pdf(pdf_path)

    # interactive chat
    print("\n=== PDF Chat System ===")
    print("Type 'quit' to exit\n")

    while True:
        question = input("Ask a question about the PDF: ").strip()

        if question.lower() == "quit":
            break

        if question:
            print("\nAnswer:")
            print(rag.chat(question))
            print("-" * 50)


if __name__ == "__main__":
    main()
