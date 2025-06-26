from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_weaviate import WeaviateVectorStore

# Recharger l’index FAISS depuis le disque
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

import weaviate
import weaviate.classes.config as wvcc
# client = weaviate.Client("http://localhost:8080")  # Assurez-vous que Weaviate tourne
print(weaviate.__version__)
# ✅ CONNEXION WEAVIATE V4
print("\n💾 Connexion à Weaviate...")
client = weaviate.connect_to_local(skip_init_checks=True)

# 2. Connecter le client à Weaviate
client = weaviate.connect_to_local(
    host="localhost",
    port=8080,
    skip_init_checks=True
)

# 3. Charger le vectorstore existant
vectorstore = WeaviateVectorStore(
    client=client,
    index_name="qwanza_docs",
    text_key="content",
    embedding=embeddings,
    attributes=["source", "page"]
)
# vectorstore = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)

# Init LLM
# llm = OllamaLLM(model="mistral")

def get_llm(model_name: str = "llama3.2"):
    return OllamaLLM(model=model_name)

llm = OllamaLLM(model="llama3.2")

# Prompt
template = """Réponds à la question suivante en te basant uniquement sur le contexte fourni. 

Context: {context}

Question: {question}

Réponds uniquement à l'aide des informations présentes dans le contexte. Si tu ne peux pas répondre à la question avec les informations disponibles, dis : "Je ne peux pas répondre à cette question avec les informations disponibles."

Réponse:"""

prompt = PromptTemplate(template=template, input_variables=["context", "question"])

# Chaîne RAG
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt 
    | llm 
    | StrOutputParser()
)

def query_documents(question: str, model_name: str = "llama3.2") -> str:
    try:
        llm = get_llm(model_name)
        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt 
            | llm 
            | StrOutputParser()
        )

        # return rag_chain.invoke(question)
    
         # 1. RAG avec contexte
        rag_response = rag_chain.invoke(question).strip()
        
        # 2. Vérifie si le modèle dit qu’il ne peut pas répondre
        if "Je ne peux pas répondre à cette question avec les informations disponibles." in rag_response:
            # Fallback vers LLM sans contexte
            return llm.invoke(question).strip()
        
        return rag_response
    
    except Exception as e:
        return f"Erreur lors de la génération : {str(e)}"
    
# if __name__ == "__main__":
#     print("\nSystème RAG initialisé. Vous pouvez poser des questions sur les expertises du cabinet QWANZA, ses missions, ou ses domaines d'intervention.")
#     print("Tapez 'quit' pour quitter.")
#     print("Assurez-vous que le service Ollama est actif avant de poser des questions.")
#     print("\nExemples de questions que vous pouvez poser :")
#     print("- Quelles sont les expertises de QWANZA en transformation digitale ?")
#     print("- Quels secteurs sont couverts par les missions de QWANZA ?")
#     print("- Quelle est l'approche de QWANZA pour optimiser les coûts informatiques ?")
#     print("- Quels sont les bénéfices de la méthodologie Lean utilisée par QWANZA ?")
#     print("- En quoi consiste l'offre Smart Support ?")
#     print("- Quels partenaires académiques collaborent avec QWANZA ?")
    
#     while True:
#         question = input("\nEnter your question: ")
#         if question.lower() == 'quit':
#             break
#         if not question.strip():
#             continue
            
#         try:
#             print("\nSearching for answer...")
#             response = query_documents(question)
#             print("\nAnswer:", response)
#         except KeyboardInterrupt:
#             print("\nExiting...")
#             break
#         except Exception as e:
#             print(f"Error: {str(e)}")