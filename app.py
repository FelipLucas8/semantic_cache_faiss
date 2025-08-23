from flask import Flask, request, jsonify
import os
import urllib.parse
from models import db
from semantic_cache import SemanticCache
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

# Configure Database URI:
params = urllib.parse.quote_plus(
    f"DRIVER={os.getenv('DB_DRIVER')};SERVER={os.getenv('DB_SERVER')};DATABASE={os.getenv('DB_NAME')};UID={os.getenv('DB_USERNAME')};PWD={os.getenv('DB_PASSWORD')};")

# initialization
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

# db start
db.init_app(app)


def cleanup_faiss_index():
    with app.app_context():
        faiss_semantic_class = SemanticCache()
        faiss_semantic_class.cleanup_faiss_index()


# STARTSECTION: JOB

now = datetime.now()
one_minutes_ahead = now + timedelta(minutes=2)

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_faiss_index,
                  "cron", hour=one_minutes_ahead.hour, minute=one_minutes_ahead.minute)
scheduler.start()

# ENDSECTION: JOB

# embedding_model = AzureOpenAI(
#     api_key=os.getenv("AZ_AOAI_EMBEDDINGS_API_KEY"),
#     api_version=os.getenv('AZ_AOAI_EMBEDDINGS_API_VERSION'),
#     azure_endpoint=os.getenv('AZ_AOAI_EMBEDDINGS_BASE_URL')
# )

# embeddins_dim = 1536  # the fixed dimension length of the 'text-embedding-ada-002' model

# cache_data = []
# indices = {}


# def get_embedding(text):
#     response = embedding_model.embeddings.create(
#         input=[text],
#         model="text-embedding-ada-002"
#     )
#     return response.data[0].embedding


# def semantic_cache_get(query, threshold=0.90):
#     index_file_path = 'faiss_index.index'
#     if not os.path.exists(index_file_path):
#         return None

#     query_vec = get_embedding(query)
#     index = faiss.read_index(index_file_path)
#     query_vec = np.array(query_vec).astype('float32').reshape(1, -1)
#     D, I = index.search(query_vec, k=1)
#     similarity = 1 - D[0][0] / 2
#     if similarity >= threshold:
#         vector_index = I[0][0].item()
#         original_item = db.session.query(VectorMapping).filter(
#             VectorMapping.vector_index == vector_index).first()

#         if original_item:
#             return {
#                 'content': original_item.content,
#                 'similarity': similarity.item()
#             }

#     return None


# def semantic_cache_set(query, answer):
#     query_vec = get_embedding(query)
#     dimensions = len(query_vec)

#     query_vec = np.array(query_vec).astype('float32')
#     # Reshape to (number of dimensions, the length of the itens in the array)
#     query_vec = query_vec.reshape(1, -1)

#     index_file_path = 'faiss_index.index'
#     if not os.path.exists(index_file_path):
#         index = faiss.IndexFlatL2(dimensions)
#         faiss.write_index(index, index_file_path)

#     index = faiss.read_index(index_file_path)
#     index.add(query_vec)
#     vector_index = index.ntotal - 1  # FAISS starts to index from zero, so the -1 here

#     faiss.write_index(index, index_file_path)

#     new_mapping = VectorMapping(
#         vector_index=vector_index, content=answer)
#     db.session.add(new_mapping)
#     db.session.commit()


@app.route("/query", methods=["POST"])
def query():

    try:
        data = request.json
        user_query = data.get("query", "Why is the capital of Malta?")

        semantic_cache = SemanticCache()

        cached_answer = semantic_cache.semantic_cache_get(
            query=user_query, user_id=48)
        if cached_answer:
            return jsonify({"answer": cached_answer['content'], 'similarity': cached_answer['similarity'], "source": "cache"})

        # computed_answer = f"A capital de Malta é Valleta"
        computed_answer = {
            "answer": f"The Malta's capital is Valleta",
            "cacheable": "yes",
            "scope": "global"
        }

        if computed_answer['cacheable'] == 'yes':
            return semantic_cache.semantic_cache_set(
                user_query, computed_answer['answer'], 48, computed_answer['scope'])

        return jsonify({"answer": computed_answer['answer'], "source": "computed"}), 200

    except Exception as e:
        print("erro: ", str(e))
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
