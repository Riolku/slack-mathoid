import flask, requests

from flask import request, abort

from sympy import preview
from base64 import b64encode, b64decode
from threading import Lock
import time

auth_url = 'https://slack.com/oauth/v2/authorize'
client_id, client_secret = open("../oauth.txt", "r").read().splitlines()

app = flask.Flask(__name__)
  
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
        
    r = requests.post(form['response_url'], json = dict(
      text = 'Psst! I can do much more than just replying to your message.' + \
        ' If you give me permission, I can instead reply as you, making the chat much cleaner.' + \
        ' If this interests you, click ' + \
        '<{aurl}?client_id={cid}&user_scope={scopes}|here> to give me permission.'.format(aurl = auth_url, cid = client_id, scopes = scopes),
      mrkdwn = "true"
    ))
        
  except RuntimeError as e:
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
    app.run(port = 4000)
