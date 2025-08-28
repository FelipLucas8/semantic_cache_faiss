# Semantic Cache with FAISS

This project implements a **semantic cache system** using **FAISS** for vector similarity search and **SQL Server** for metadata storage.  
It allows caching of embeddings for faster semantic search and supports scheduled cleanup jobs to remove unused or outdated vectors.  

---

## 🚀 Features
- Embedding generation using [SentenceTransformers](https://www.sbert.net/).
- FAISS-based semantic similarity search.
- SQLAlchemy integration with SQL Server for metadata persistence.
- Background jobs with APScheduler for automatic cleanup.
- REST API built with Flask for cache interaction.

---

## 📦 Installation

### Requirements
- Python 3.9+
- SQL Server
- pipenv or venv for virtual environment

### Setup
```bash
# Clone the repository
git clone https://github.com/FelipLucas8/semantic_cache_faiss.git
cd semantic_cache_faiss

# Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ Configuration
Environment variables:
```env
DB_SERVER=localhost
DB_NAME=semantic_cache
DB_DRIVER={ODBC Driver 17 for SQL Server}
FLASK_ENV=development
```

---

## ▶️ Usage
Run the Flask app:
```bash
python app.py
```

The API will start at `http://localhost:5000`.

---

# 📖 README em Português

Este projeto implementa um **sistema de cache semântico** utilizando o **FAISS** para busca por similaridade vetorial e o **SQL Server** para armazenamento de metadados.  
Ele permite armazenar embeddings para buscas semânticas rápidas e suporta jobs agendados para limpar vetores não utilizados ou desatualizados.  

---

## 🚀 Funcionalidades
- Geração de embeddings com [SentenceTransformers](https://www.sbert.net/).
- Busca semântica baseada em FAISS.
- Integração com SQLAlchemy e SQL Server para persistência.
- Jobs em segundo plano com APScheduler para limpeza automática.
- API REST construída com Flask para interação com o cache.

---

## 📦 Instalação

### Requisitos
- Python 3.9+
- SQL Server
- pipenv ou venv para ambiente virtual

### Configuração
```bash
# Clonar o repositório
git clone https://github.com/FelipLucas8/semantic_cache_faiss.git
cd semantic_cache_faiss

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# Instalar dependências
pip install -r requirements.txt
```

---

## ⚙️ Configuração
Variáveis de ambiente:
```env
DB_SERVER=localhost
DB_NAME=semantic_cache
DB_DRIVER={ODBC Driver 17 for SQL Server}
FLASK_ENV=development
```

---

## ▶️ Uso
Executar o Flask:
```bash
python app.py
```

A API estará disponível em `http://localhost:5000`.

---
