from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import os
from ppt_loader import PowerPointLoader

import os
from traceback import print_list
import pandas as pd
from langchain_weaviate import WeaviateVectorStore
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from ppt_loader import PowerPointLoader

def index_document(pdf_path: str, index_path: str = "faiss_index") -> FAISS:
    """
    Charge un fichier PDF, le découpe, l'encode et l'indexe dans FAISS.
    
    Args:
        pdf_path (str): Chemin vers le fichier PDF à indexer.
        index_path (str): Dossier où sauvegarder l'index FAISS.

    Returns:
        FAISS: L'objet FAISS vectorstore généré.
    """
    print(f"📥 Chargement du document : {pdf_path}")

    # Initialiser les embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # Traiter les fichiers PDF
    if pdf_path.lower().endswith('.pdf'):
        print(f"Chargement du PDF: {pdf_path}")
        loader = UnstructuredPDFLoader(pdf_path, mode="elements")
        try:
            documents = loader.load()
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {pdf_path}: {str(e)}")
            
    # Traiter les fichiers PowerPoint
    elif pdf_path.lower().endswith(('.ppt', '.pptx')):
        print(f"Chargement du PowerPoint: {pdf_path}")
        loader = PowerPointLoader(pdf_path)
        try:
            documents = loader.load()
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {pdf_path}: {str(e)}")

    #✅ SEMANTIC CHUNKING
    print("\n🧠 Découpage sémantique intelligent...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    text_splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile"
    )

    # Ne pas découper les documents PowerPoint qui sont déjà découpés par slide
    chunks = []
    for doc in documents:
        if doc.metadata.get('type') == 'powerpoint':
            chunks.append(doc)
        else:
            chunks.extend(text_splitter.split_documents([doc]))

    print(f"✅ {len(chunks)} chunks créés.")

    # ✅ CRÉATION DU VECTOR STORE AVEC WEAVIATE
    print("\n💾 Enregistrement dans Weaviate...")
    import weaviate
    import weaviate.classes.config as wvcc
    # client = weaviate.Client("http://localhost:8080")  # Assurez-vous que Weaviate tourne
    print(weaviate.__version__)

    # ✅ CONNEXION WEAVIATE V4
    print("\n💾 Connexion à Weaviate...")
    client = weaviate.connect_to_local(skip_init_checks=True)

    # ✅ CRÉATION DE L'INDEX AVEC SYNTAXE V4
    try:
        if not client.collections.exists("qwanza_docs"):
            collection = client.collections.create(
                name="qwanza_docs",
                properties=[
                    wvcc.Property(
                        name="content",
                        data_type=wvcc.DataType.TEXT
                    ),
                    wvcc.Property(
                        name="source",
                        data_type=wvcc.DataType.TEXT
                    ),
                    wvcc.Property(
                        name="page",
                        data_type=wvcc.DataType.NUMBER
                    )
                ]
            )
        print("✅ Collection Weaviate prête")
    except Exception as e:
        print(f"❌ Erreur création collection: {str(e)}")
        client.close()
        exit(1)

    # Nettoyage des métadonnées des chunks
    for chunk in chunks:
        # On ne garde que les métadonnées essentielles
        cleaned_metadata = {
            "source": chunk.metadata.get("source", ""),
            "page": chunk.metadata.get("page", 0)
        }
        chunk.metadata = cleaned_metadata

    # UTILISATION AVEC LANGCHAIN
    vectorstore = WeaviateVectorStore(
        client=client,
        index_name="qwanza_docs",
        text_key="content",
        embedding=embeddings,
        attributes=["source", "page"]  # Spécifier les attributs à stocker
    )

    try:
        print("\n💾 Ajout des documents dans Weaviate...")
        vectorstore.add_documents(chunks)
        print(f"✅ {len(chunks)} chunks ajoutés avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des documents : {str(e)}")
        client.close()
        exit(1)

    # print(f"📊 Nombre d'objets dans la collection : {client.collections.get('qwanza_docs').count_objects()}")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}:")
        print(chunk.page_content)
        print("="*40)

    # print("✅ Index Weaviate créé.")

    collection = client.collections.get("qwanza_docs")
    results = collection.query.fetch_objects(limit=10)

    for i, obj in enumerate(results.objects):
        print(f"Objet {i}:")
        print(obj.properties)


    print(vars(chunks[0]))
    print(chunks[0].page_content)
    print(chunks[0].metadata)
    print("walouuu")

    # if os.path.exists(index_path):
    #     print(f"📂 Chargement de l'index existant depuis : {index_path}")
    #     vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    #     vectorstore.add_documents(splits)
    # else:
    #     print("📁 Aucun index existant trouvé, création d'un nouveau.")
    #     vectorstore = FAISS.from_documents(splits, embeddings)

    # # Sauvegarder la nouvelle version de l'index
    # vectorstore.save_local(index_path)
    # print(f"✅ Index mis à jour dans : {index_path}")

    return vectorstore