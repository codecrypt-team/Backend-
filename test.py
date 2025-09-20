# import requests

# BASE = "http://127.0.0.1:5000/"

# response = requests.get(BASE)

# print("Status Code:", response.status_code)
# print("Raw Response:", response.text)


import requests

url = "http://127.0.0.1:5000/chat"
data = {"message": "my girlfriend is going to USA next month but i failed in jee and i got compartment in mathematics too what should i do and is there any chance for me to go to USA with her"}

response = requests.post(url, json=data)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
