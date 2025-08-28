from flask import Flask, request, jsonify
import os
from models import db
from semantic_cache import SemanticCache
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

server = os.getenv("DB_SERVER", 'localhost')
db_name = os.getenv("DB_NAME", 'semantic_cache')
driver = os.getenv("DB_DRIVER", '{ODBC Driver 17 for SQL Server}')

is_local = os.getenv("FLASK_ENV", "development") == "development"

if is_local:
    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={db_name};Trusted_Connection=yes;"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={conn_str}"


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

@app.route("/query", methods=["POST"])
def query():

    try:
        data = request.json
        user_query = data.get("query", "Why is the capital of Malta?")

        semantic_cache = SemanticCache()

        cached_answer = semantic_cache.semantic_cache_get(
            query=user_query, user_id=1)
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
                user_query, computed_answer['answer'], 1, computed_answer['scope'])

        return jsonify({"answer": computed_answer['answer'], "source": "computed"}), 200

    except Exception as e:
        print("erro: ", str(e))
        return jsonify({"erro": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
