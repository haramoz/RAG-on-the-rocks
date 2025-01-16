# create env:
pyenv install 3.10
pyenv virtualenv 3.10 rag-on-the-rocks
pyenv virtualenvs

pyenv activate rag-on-the-rocks

# requirements

pip install -r requirements.txt

We are going for langchain, streamlit, pypdf2, faiss or Chroma and ollama server
