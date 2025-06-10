import json
from channels.generic.websocket import AsyncWebsocketConsumer
import requests

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_message = data['message']
        
        # Call AI model (Replace with actual API call)
        bot_response = self.get_ai_response(user_message)

        # Send response back to frontend
        await self.send(text_data=json.dumps({
            'message': bot_response
        }))

    def get_ai_response(self, prompt):
        """ Replace with Groq API or Llama3/Mixtral call """
        API_URL = "https://api.groq.com/openai/v1/chat/completions"  # Replace with actual URL
        HEADERS = {"Authorization": "Bearer YOUR_API_KEY"}
        DATA = {
            "model": "mixtral",
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(API_URL, json=DATA, headers=HEADERS)
            return response.json()["choices"][0]["message"]["content"]
        except:
            return "Sorry, I'm having trouble processing your request."
