from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restful import Api, Resource
from pymongo import MongoClient
import google.generativeai as genai
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app)
api = Api(app)

# MongoDB connection using the environment variable
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set. Please create a .env file.")

client = MongoClient(mongo_uri)

# Connect to the database specified in the MongoDB URI ("todo")
db = client.get_default_database()
chat_collection = db["chats"]

# Google Gemini API configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "YOUR API KEY HERE"))

class Chatbot(Resource):

    def post(self):
        """
        Handles user messages, gets an AI response, and saves both to the database.
        Returns the entire updated chat history.
        """
        data = request.get_json()
        user_id = data.get("user_id", "guest")
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Save the user's message with a timestamp
        user_message_data = {
            "type": "user",
            "message": user_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"chat_history": user_message_data}},
            upsert=True
        )

        # Get AI response from Gemini API
        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            response = model.generate_content(user_message)
            ai_message = response.text
        except Exception as e:
            # Handle potential API errors gracefully
            return jsonify({"error": f"AI API error: {str(e)}"}), 500

        # Save the AI's response with a timestamp
        ai_message_data = {
            "type": "ai",
            "message": ai_message,
            "timestamp": datetime.utcnow().isoformat()
        }
        chat_collection.update_one(
            {"user_id": user_id},
            {"$push": {"chat_history": ai_message_data}},
            upsert=True
        )

        # Retrieve the updated chat history to send back
        updated_chat_doc = chat_collection.find_one({"user_id": user_id})
        
        return jsonify({
            "user_id": updated_chat_doc["user_id"],
            "chat_history": updated_chat_doc["chat_history"]
        })

    def get(self):
        """
        Fetches and returns the saved chat history for a user.
        """
        user_id = request.args.get("user_id", "guest")
        chat_doc = chat_collection.find_one({"user_id": user_id})

        if not chat_doc:
            return jsonify({"message": "No chat history found"}), 404

        # Return the entire chat history in a clean format
        return jsonify({
            "user_id": chat_doc["user_id"],
            "chat_history": chat_doc["chat_history"]
        })

api.add_resource(Chatbot, '/chat')

