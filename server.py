from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
from pathlib import Path
from main import SimplePDFRAG
import json
import asyncio

app = FastAPI(title="ClassDocs - Plataforma Educacional")

UPLOAD_DIR = "uploads"
STATIC_DIR = "static"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

rag = SimplePDFRAG()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>ClassDocs - Plataforma Educacional</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #60a5fa 100%); min-height: 100vh; color: white;">
            <div style="padding: 40px;">
                <h1 style="font-size: 3rem; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">📚 ClassDocs</h1>
                <p style="font-size: 1.2rem; margin-bottom: 50px; opacity: 0.9;">Plataforma Educacional com IA</p>
                <div style="margin: 50px;">
                    <a href="/teacher" style="display: inline-block; padding: 20px 40px; margin: 10px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 15px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3); transition: all 0.3s; font-weight: 600;">👨‍🏫 Área do Professor</a>
                    <a href="/student" style="display: inline-block; padding: 20px 40px; margin: 10px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 15px; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.3); transition: all 0.3s; font-weight: 600;">🎓 Área do Estudante</a>
                </div>
            </div>
        </body>
    </html>
    """

@app.get("/teacher")
async def teacher_view():
    return FileResponse(f"{STATIC_DIR}/teacher.html")

@app.get("/student")
async def student_view():
    return FileResponse(f"{STATIC_DIR}/student.html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Reload RAG with all PDFs in uploads folder
    rag.load_folder(UPLOAD_DIR)
    
    return {"message": f"Arquivo {file.filename} enviado com sucesso", "filename": file.filename}

@app.get("/documents")
async def list_documents():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.pdf')]
    return {"documents": files}

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        # Reload RAG with remaining PDFs
        rag.load_folder(UPLOAD_DIR)
        return {"message": f"Documento {filename} excluído com sucesso"}
    else:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            question = message_data.get("message", "")
            
            if question:
                # Get answer from RAG
                answer = rag.chat(question)
                
                response = {
                    "type": "answer",
                    "message": answer
                }
                
                await manager.send_personal_message(json.dumps(response), websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Initialize RAG with any existing PDFs
if os.path.exists(UPLOAD_DIR):
    rag.load_folder(UPLOAD_DIR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)