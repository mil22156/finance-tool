import os
from dotenv import load_dotenv
from database.db import init_registry
from flask import Flask

load_dotenv()



app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

REGISTRY_PATH = os.path.join('data', 'registry.db')
init_registry(REGISTRY_PATH)

@app.route('/')
def index():
    return 'Finance Tool is running.'

if __name__ == '__main__':
    app.run(debug=True)
