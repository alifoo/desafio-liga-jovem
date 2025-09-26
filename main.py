import os
import PyPDF2
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
import glob
from pathlib import Path

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


class SimplePDFRAG:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        # load embedding model
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.chunks = []
        self.embeddings = []
        self.chunk_sources = []

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
        pdf_chunks = self.chunk_text(text)
        
        # add to existing chunks with source tracking
        filename = Path(pdf_path).name
        for chunk in pdf_chunks:
            self.chunks.append(chunk)
            self.chunk_sources.append(filename)
        
        print(f"Added {len(pdf_chunks)} chunks from {filename}")

        # regenerate embeddings for all chunks
        self.embeddings = self.embedder.encode(self.chunks)
        print(f"Total chunks: {len(self.chunks)}")

    def load_folder(self, folder_path):
        """Load all PDFs from a folder"""
        self.chunks = []
        self.embeddings = []
        self.chunk_sources = []
        
        pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))
        
        if not pdf_files:
            print("No PDF files found in folder")
            return
            
        for pdf_path in pdf_files:
            self.load_pdf(pdf_path)
        
        print(f"Loaded {len(pdf_files)} PDF files with {len(self.chunks)} total chunks")

    def retrieve_relevant_chunks(self, query, top_k=3):
        """Retrieve most relevant chunks for query with source information"""
        query_embedding = self.embedder.encode([query])

        # calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        # get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        relevant_chunks_with_sources = []
        for i in top_indices:
            chunk_data = {
                'content': self.chunks[i],
                'source': self.chunk_sources[i],
                'similarity': similarities[i]
            }
            relevant_chunks_with_sources.append(chunk_data)
        
        return relevant_chunks_with_sources

    def chat(self, question):
        """Chat with the PDF content using Gemini"""
        if not self.chunks:
            return "Olá! 👋 Ainda não temos materiais da aula carregados no sistema. Por favor, peça ao seu professor para enviar os documentos da aula para que eu possa ajudá-lo com suas dúvidas."

        # retrieve relevant context with sources
        relevant_chunks_data = self.retrieve_relevant_chunks(question)
        
        # build context with source information
        context_parts = []
        sources_used = set()
        for chunk_data in relevant_chunks_data:
            source = chunk_data['source']
            content = chunk_data['content']
            context_parts.append(f"[Fonte: {source}]\n{content}")
            sources_used.add(source)
        
        context = "\n\n".join(context_parts)
        sources_list = ", ".join(sorted(sources_used))

        # create prompt
        prompt = f"""Você é um assistente de ensino inteligente do ClassDocs, auxiliando estudantes durante a aula. Sua função é ajudar os alunos a compreender melhor o conteúdo dos materiais didáticos fornecidos pelo professor.

INSTRUÇÕES IMPORTANTES:
- Responda como um professor assistente, de forma didática e educativa
- Use linguagem clara e adequada para estudantes
- Explique conceitos de forma pedagógica quando possível
- Incentive o aprendizado e a curiosidade
- Mantenha um tom respeitoso e encorajador
- Se a pergunta não estiver relacionada ao contexto dos documentos, informe educadamente que só pode ajudar com o conteúdo da aula
- SEMPRE mencione as fontes dos documentos quando basear sua resposta neles
- Use o formato: "Baseado no documento [nome_do_arquivo]..." quando referenciar informações específicas

MATERIAIS DISPONÍVEIS DA AULA: {sources_list}

CONTEXTO DOS MATERIAIS DA AULA:
{context}

PERGUNTA DO ESTUDANTE: {question}

COMPORTAMENTO ESPERADO:
1. Se você encontrar a informação no contexto, responda de forma didática e educativa, mencionando sempre as fontes dos documentos.

2. Se a pergunta estiver RELACIONADA ao tema geral dos materiais (mesmo que a informação específica não esteja nos documentos), seja útil:
   - Informe que a informação específica não está nos materiais da aula
   - Forneça uma explicação educativa geral sobre o tópico perguntado (usando seu conhecimento geral)
   - Deixe claro que esta é uma explicação geral e que o estudante deve verificar com o professor se está alinhada com o conteúdo específico da disciplina
   - Use o formato: "Embora essa informação específica não esteja detalhada nos materiais disponíveis ({sources_list}), posso te ajudar com uma explicação geral..."
   - Termine sempre sugerindo: "Recomendo que você confirme essas informações com o professor para garantir que estão alinhadas com o conteúdo específico da disciplina."

3. EXCEÇÃO IMPORTANTE: Se a pergunta for sobre um assunto COMPLETAMENTE DIFERENTE do tema dos materiais da aula (exemplo: pergunta de biologia quando os materiais são de programação), responda apenas:
   "Desculpe, não encontrei essa informação nos materiais da aula disponíveis ({sources_list}). Esta pergunta parece estar fora do escopo do conteúdo desta disciplina. Recomendo que você consulte o professor ou os materiais adequados para esse tópico."

AVALIE SEMPRE se a pergunta tem relação com o tema geral dos materiais antes de decidir qual comportamento seguir.

RESPOSTA:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Erro ao gerar resposta: {str(e)}"


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
