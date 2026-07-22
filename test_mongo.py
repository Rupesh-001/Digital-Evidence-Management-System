from pymongo import MongoClient
import certifi

uri = "mongodb+srv://varmarupesh101_db_user:YOUR_PASSWORD@cluster0.d7unquw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(
        uri,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000
    )
    print(client.admin.command("ping"))
    print("Connected!")
except Exception as e:
    print("Error:", e)