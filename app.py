from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
import google.generativeai as genai  

app = Flask(__name__)
CORS(app)
api = Api(app)

client = MongoClient("mongodb://localhost:27017/")  
db = client["career_advisor"]
chat_collection = db["chats"]
jwt = JWTManager(app)

genai.configure(api_key="YOUR API KEY HERE")

# @app.route('/')
# def home():
#     return render_template("index.html")

class Chatbot(Resource):
    
    def post(self):
        data = request.get_json()
        user_id = data.get("user_id", "guest") 
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # AI response
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(user_message)
        ai_message = response.text

        # user saved message
        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"chat_history": {"role": "user", "message": user_message}}},
            upsert=True
        )

        # AI saved message
        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"chat_history": {"role": "ai", "message": ai_message}}},
            upsert=True
        )

        return jsonify({"response": ai_message})

    # GET: saved chats fetching
    def get(self):
        user_id = request.args.get("user_id", "guest")   # query param will bring id 
        chat_doc = chat_collection.find_one({"user_id": user_id})

        if not chat_doc:
            return jsonify({"message": "No chat history found"}), 404

        # sending to frontend in a clean format 
        return jsonify({
            "user_id": chat_doc["user_id"],
            "chat_history": chat_doc["chat_history"]
        })

api.add_resource(Chatbot, '/chat')

if __name__ == "__main__":
    app.run(debug=True)
