from utils import LockedDict, LockedCache, LockedJSON, latexify

from api import get_error_json, get_psst_json, get_success_json, make_json_resp

from app import app

from flask import request, Response, abort

from base64 import b64decode

import requests

cache = LockedCache()

@app.route("/", methods = ["POST"])
def index():
  form = request.form
  
  inp = form['text']
  
  try:
    img = latexify(inp)
  except RuntimeError as e:
    return make_json_resp(get_error_json(e.args[0]))
  
  cache[inp] = img
  
  r = requests.post(form['response_url'], json = get_success_json(inp))
    
  assert r.ok
  
  return make_json_resp(get_psst_json())

@app.route("/i/<path:inp>")
def serve_image(inp):
  try:
    inp = b64decode(inp.encode("utf-8")).decode("utf-8")
  except:
    abort(400)
    
  img = cache[inp]
  
  if img is None:
    try:
      img = latexify(inp)
    except RuntimeError as e:
      abort(400)
      
    cache[inp] = img
    
  return Response(img, mimetype = "image/png")