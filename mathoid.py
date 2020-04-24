import flask, requests

from flask import request, abort

from sympy import preview
from base64 import b64encode, b64decode
from threading import Lock
import time

from io import BytesIO

app = flask.Flask(__name__)

lock = Lock()

cache = {}

def poke_cache(inp, img):
  with lock:
    todel = []
    
    for k, v in cache.items():
      # Cache timeout of 1 minute
      if time.time() - v['time'] > 60:
        todel.append(k)
        
    for k in todel: del cache[k]
    
    cache[inp] = dict(img = img, time = time.time())

def peek_cache(inp):
  with lock:
    if inp not in cache:
      return None
    
    return cache[inp]['img']

def latexify(texstr):
  # Mathoid server
  r = requests.post("http://localhost:10044/png", data = dict(q = texstr))
  
  if r.status_code == 400:
    raise Exception(r.json()['error'])
    
  return r.content
  
@app.route("/", methods = ["POST"])
def index():
  form = request.form
  
  inp = form['text']

  try:
    img = latexify(inp)
    
    res = flask.json.dumps({
      "text" : inp,
      "response_type" : "in_channel",
      "blocks" : [{
        "type": "image",
        "image_url": "https://slack-mathoid.kgugeler.ca/i/%s" % b64encode(inp.encode("utf-8")).decode("utf-8"), 
        "alt_text": inp
      }]
    })
    
    poke_cache(inp, img)
    
  except Exception as e:
    res = flask.json.dumps({
      "text" : "Your latex couldn't be parsed.",
      "response_type" : "ephemeral",
      "blocks" : [{
        "type" : "section",
        "text" : {
          "type" : "plain_text",
          "text" : "Your latex couldn't be parsed. The error we received was '%s'." % e.args[0]
        }
      }]
    })
          
  return flask.Response(res, mimetype = "application/json")

@app.route("/i/<path:inp>")
def serve_image(inp):
  try:
    inp = b64decode(inp.encode("utf-8")).decode("utf-8")
  except:
    abort(400)
  
  img = peek_cache(inp)
  
  if img is None:
    try:
      img = latexify(inp)
    except:
      abort(400)
    
    poke_cache(inp, img)
  
  return flask.Response(img, mimetype = "image/png")

if __name__ == "__main__":
    app.run(port = 9000)
