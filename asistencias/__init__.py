from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os

# crear app
app = Flask(__name__)
csrf = CSRFProtect(app)

# recargar las plantillas si se modifican
app.config["TEMPLATES_AUTO_RELOAD"] = True

if not os.environ.get("SECRET_KEY"):
	raise RuntimeError("SECRET_KEY no establecida")
else:
	app.secret_key = os.environ.get("SECRET_KEY")

# no guardar las respuestas en el cache
@app.after_request
def after_request(response):
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = 0
	response.headers["Pragma"] = "no-cache"
	return response

import asistencias.rutas
