from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from rag import query_documents
from index_document import index_document  # si tu la mets dans un autre fichier
import tempfile
import shutil

app = FastAPI()
app = FastAPI(
    title="Qwanza RAG API",
    description="API pour poser des questions à partir de documents vectorisés.",
    version="1.0.0"
)
# Define a request model
class InputData(BaseModel):
    text: str
    model: str = "llama3.2"  # par défaut

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "API is running"}


@app.post("/index_pdf")
async def index_uploaded_pdf(pdf_file: UploadFile = File(...)):
    try:
        # Sauvegarder temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            shutil.copyfileobj(pdf_file.file, tmp)
            pdf_path = tmp.name

        # Indexer
        vectorstore = index_document(pdf_path)

        if vectorstore is None:
            return {"status": "error", "message": "Échec de l'indexation"}

        return {"status": "indexed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/predict")
def predict(input_data: InputData):
    question = input_data.text.strip()
    model = input_data.model

    if not question:
        return {"result": "⚠️ Aucune question fournie."}

    try:
        # 🔍 Appel de la fonction RAG
        response = query_documents(question, model_name=model)
        return {"result": response}
    except Exception as e:
        return {"result": f" Erreur lors de la génération de la réponse : {str(e)}"}