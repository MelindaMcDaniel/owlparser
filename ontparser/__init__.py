from flask import Flask, current_app
app = Flask(__name__)

import ontparser.restapi
import ontparser.views
