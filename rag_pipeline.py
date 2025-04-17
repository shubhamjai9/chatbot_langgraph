from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, OllamaEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from dotenv import load_dotenv
import os
import shutil
from scrap import get_processed_text, url_extract

curr_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHROMA_PATH = curr_path + "/database/"

load_dotenv(curr_path + "/.env", override=True)

print(curr_path, os.getenv("OPENAI_API_KEY"))


def split_text(document: str):
    """
    Split the text content of the given list of Document objects into smaller chunks.
    Args:
      document (str): Document representing text chunks to split.
    Returns:
      list[Document]: List of Document objects representing the split text chunks.
    """
    # Initialize text splitter with specified parameters
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Size of each chunk in characters
        chunk_overlap=100,  # Overlap between consecutive chunks
        length_function=len,
        add_start_index=True,  # Flag to add start index to each chunk
    )

    # Split documents into smaller chunks using text splitter
    chunks = text_splitter.split_text(document)
    print(f"Split {len(document)} documents into {len(chunks)} chunks.")

    return chunks  # Return the list of split text chunks


def load_store(embed: str = os.getenv("MODEL")):
    if embed == "mxbai":
        vector_store = Chroma(
            persist_directory=f"{CHROMA_PATH}/mxbai",
            collection_name="test",
            embedding_function=OllamaEmbeddings(model="mxbai-embed-large:latest"),
        )
    else:
        vector_store = Chroma(
            persist_directory=f"{CHROMA_PATH}/openai",
            collection_name="test",
            embedding_function=OpenAIEmbeddings(),
        )
    return vector_store


def save_to_chroma(chunks: list[str], product: str, url: str, vector_store):
    """
    Save the given list of Document objects to a Chroma database.
    Args:
    document (str): Document representing text chunks to save.
    Returns:
    None
    """

    # chunks = split_text(document)
    metadata = []
    ids = []
    c = 0
    for chunk in chunks:
        metadata.append({"product": product, "url": url})
        ids.append(product + url + str(c))
        c += 1
    vector_store.add_texts(
        chunks,
        metadatas=metadata,
        ids=ids,
    )

    # Persist the database to disk
    vector_store.persist()
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
    return vector_store


def url_data_updation(urls: list[str], product: str, vector_store):
    success_url = []
    failed_url = []
    if type(urls) != list or len(urls) < 1:
        return {
            "status": "Failure",
            "indexed_url": [],
            "failed_url": [],
            "error": "Please provide valid list of urls",
        }
    for url in urls:
        try:
            raw_data = url_extract(url)
            if type(raw_data) == dict:
                if raw_data["status"] == False:
                    return raw_data
            text = get_processed_text(raw_data, url)
            # if os.getenv("MODEL") == "ColBERT":
            #     save_to_ragatouille(
            #         text, {"product": product, "url": url}, vector_store
            #     )
            # else:
            documents = split_text(text)
            save_to_chroma(documents, product, url, vector_store)
            success_url.append(url)
        except Exception as e:
            print("Error at url extraction", e)
            failed_url.append(url)
    return {"status": "success", "indexed_url": success_url, "failed_url": failed_url}
    # except Exception as e:
    #     return {}


if __name__ == "__main__":
    urls = urls = [
        "https://www.hdfcbank.com/personal/borrow/popular-loans/personal-loan",
        "https://www.hdfcbank.com/personal/borrow/popular-loans/educational-loan/education-loan-for-foreign-education/eligibility",
    ]
    product = "loan"
    vector_store = load_store()
    print(vector_store)
    print(url_data_updation(urls, product, vector_store))
