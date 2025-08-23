import faiss
import numpy as np
import os
from models import db, VectorMapping, User
from flask import jsonify
import threading
from datetime import datetime, timedelta, timezone
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"  # 1024-d, multilingual
MAX_VECTORS = 3
IDLE_DAYS = 7
NUMBER_OF_K = 5
EMBEDDING_MODEL = 1024

embedding_model = SentenceTransformer(MODEL_NAME, device="cpu")

class SemanticCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:  # thread-safe
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, embedding_dimensions=EMBEDDING_MODEL):
        if not hasattr(self, 'initialized'):
            self.embedding_dimensions = embedding_dimensions
            self.query_embedding = None
            self.embedding_model = embedding_model
            self.index_name = 'semantic_cache.index'
            self.lock = threading.Lock()
            self.faiss_index = self.__build_semantic_index()
            self.initialized = True

    def get_embedding(self, text):
        if self.query_embedding:
            return self.query_embedding

        response = embedding_model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return response

    def semantic_cache_get(self, query, user_id, threshold=0.90, k=NUMBER_OF_K):
        try:
            with self.lock:
                index_file_path = self.index_name
                if not os.path.exists(index_file_path):
                    return None

                self.query_embedding = self.get_embedding(query)
                query_vec = self.__prepare_query_vectors(self.query_embedding)

                return self.__get_content_by_similarity(query_vec, user_id, threshold, k)
        except Exception as ex:
            print("Error getting the semantic cache: ", str(ex))

    def semantic_cache_set(self, query, answer, user_id, scope):
        try:
            with self.lock:
                self.query_embedding = self.get_embedding(query)
                # dimensions = len(self.query_embedding)

                prepared_vectors = self.__prepare_query_vectors(
                    self.query_embedding)

                index_file_path = self.index_name
                if not os.path.exists(index_file_path):
                    self.faiss_index = self.__build_semantic_index()

                user = (
                    db.session.query(User)
                    .filter(User.user_id == user_id)
                    .first()
                )

                if not user:
                    return jsonify({"message": "User not found"}), 404

                new_mapping = VectorMapping(
                    user_id=user_id, prompt_language=user.prompt_language, embedding=prepared_vectors.astype("float32").tobytes(), content=answer)

                if scope == "user" and user_id:
                    new_mapping.scope = "user"
                elif scope == "global":
                    new_mapping.user_id = None
                    new_mapping.scope = "global"
                else:
                    raise Exception(f"Scope not recognized: {scope}")

                db.session.add(new_mapping)
                # insert the item in the table generating the unique identifier of vector_id but not commit yet
                db.session.flush()

                self.faiss_index.add_with_ids(prepared_vectors, np.array(
                    [new_mapping.id], dtype=np.int64))

                db.session.commit()

                return jsonify({"answer": answer, "source": "computed"}), 200

        except Exception as ex:
            print("Error setting the semantic cache: ", str(ex))
            return jsonify({"Error": str(ex)}), 500

    def cleanup_faiss_index(self, max_vectors=MAX_VECTORS):
        try:
            with self.lock:
                _, has_error = self.__delete_idle_items_in_semantic_cache()
                if has_error:
                    print(
                        f"Error deleting idle items: {ex}")
                    return self.faiss_index, False

                current_count = self.faiss_index.ntotal
                print(f"Passed FAISS index contians {current_count} vectors.")

                if current_count <= max_vectors:
                    print("No cleanup needed in the semantic cache index.")
                    return False

                mapping_vectors_to_delete = db.session.query(VectorMapping)\
                    .order_by(VectorMapping.usage_count.asc())\
                    .limit(current_count - max_vectors)\
                    .all()

                for mapping_vector in mapping_vectors_to_delete:
                    db.session.delete(mapping_vector)

                db.session.commit()

                if not mapping_vectors_to_delete:
                    return False

                print("Rebuilding FAISS index to free memory...")

                self.faiss_index = self.__build_semantic_index()

                return True
        except Exception as ex:
            print("Error rebuilding the FAISS index: ", str(ex))
            return False

    def __delete_idle_items_in_semantic_cache(self, idle_days=IDLE_DAYS):
        try:
            cutoff_date = datetime.now(
                timezone.utc) - timedelta(days=idle_days)

            idle_items_to_delete = db.session.query(VectorMapping)\
                .filter(VectorMapping.updated_at < cutoff_date)\
                .all()

            if not idle_items_to_delete:
                return False, None

            for idle_item in idle_items_to_delete:
                db.session.delete(idle_item)

            db.session.commit()

            self.faiss_index = self.__build_semantic_index()
            return True, None
        except Exception as ex:
            db.session.rollback()
            return False, str(ex)

    def __build_semantic_index(self):
        faiss_index = faiss.IndexFlatL2(self.embedding_dimensions)
        new_faiss_index = faiss.IndexIDMap(faiss_index)

        saved_mapping_vectors = db.session.query(VectorMapping).all()

        index_file_path = self.index_name
        if not saved_mapping_vectors:
            faiss.write_index(new_faiss_index, index_file_path)
            return new_faiss_index

        embeddings = np.array(
            [np.frombuffer(v.embedding, dtype=np.float32) for v in saved_mapping_vectors], dtype=np.float32)
        ids = np.array(
            [v.id for v in saved_mapping_vectors], dtype=np.int64)

        new_faiss_index.add_with_ids(embeddings, ids)
        print(f"Built FAISS index with {new_faiss_index.ntotal} vectors.")

        faiss.write_index(new_faiss_index, index_file_path)
        return new_faiss_index

    def __prepare_query_vectors(self, query_vectors):
        prepared_vectors = np.array(query_vectors).astype('float32')
        # Reshape to (number of dimensions, the length of the itens in the array)
        prepared_vectors = prepared_vectors.reshape(1, -1)
        self.query_embedding = None
        return prepared_vectors

    def __get_content_by_similarity(self, query_vectors, user_id, threshold=0.90, k=NUMBER_OF_K):
        # the 5 most similar results according to the embeddings
        distances, faiss_ids = self.faiss_index.search(query_vectors, k)

        distances = distances[0].tolist()
        faiss_ids = faiss_ids[0].tolist()

        best_options = [(faiss_id, self._distance_to_similarity(distance)) for faiss_id, distance in zip(
            faiss_ids, distances) if self._distance_to_similarity(distance) >= threshold]

        if not best_options:
            return None

        best_option = max(best_options, key=lambda option: option[1])
        best_option_id = best_option[0]
        best_option_similarity = best_option[1]

        user = (
            db.session.query(User)
            .filter(User.user_id == user_id)
            .first()
        )

        sql_metadata = (
            db.session.query(VectorMapping)
            .filter(VectorMapping.id == best_option_id)
            .filter((VectorMapping.scope == 'global') | (VectorMapping.user_id == user_id))
            .filter(VectorMapping.prompt_language == user.prompt_language)
            .first()
        )

        if not sql_metadata:
            return None

        sql_metadata.usage_count += 1
        db.session.commit()

        return {
            'content': sql_metadata.content,
            'similarity': best_option_similarity
        }

    def _distance_to_similarity(self, distance):
        """
        Converts a distance value to a normalized similarity score.

        Parameters:
        distance (float): The distance value to convert.

        Returns:
        float: A similarity score between 0 and 1, where 1 indicates perfect similarity
            and 0 indicates the threshold distance.
        """
        # Normalize the distance to similarity
        similarity = 1 - distance / 2

        # Ensure the similarity score is not less than 0
        return max(similarity, 0)
