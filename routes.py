from utils import LockedCache, LockedJSON, latexify, img_cache, users

from api import get_error_json, get_psst_json, \
  get_success_json, make_json_resp, authorize_user,   \
  user_success_message, internal_error_json,  \
  revoke_token, get_authorize_url

from app import app

from flask import request, Response, abort

from base64 import b64decode

import requests

@app.route("/", methods = ["POST"])
def index():
  form = request.form
  
  inp = form['text']
  
  try:
    img = latexify(inp)
  except RuntimeError as e:
    return make_json_resp(get_error_json(e.args[0]))
  
  img_cache[inp] = img
  
  user = users[form['user_id']]
  channel = form['channel_id']
  
  if user is not None and user['type'] == 'authed':
    r = user_success_message(user['token'], channel, inp)
  else:
    r = requests.post(form['response_url'], json = get_success_json(inp))
    
  if not r.ok:
    return make_json_resp(internal_error_json('error code %d' % r.status_code))
    
  if user is not None:
    return ""
  
  return make_json_resp(get_psst_json())

@app.route("/i/<path:inp>")
def serve_image(inp):
  try:
    inp = b64decode(inp.encode("utf-8")).decode("utf-8")
  except:
    abort(400)
    
  img = img_cache[inp]
  
  if img is None:
    try:
      img = latexify(inp)
    except RuntimeError as e:
      abort(400)
      
    img_cache[inp] = img
    
  return Response(img, mimetype = "image/png")
  
@app.route("/authorize")
def serve_authorize_user():
  code = request.args.get("code")
  
  if code is None:
    abort(400)
    
  r = authorize_user(code)
  
  if not r.ok:
    abort(400)
    
  if not r.json()['ok']:
    return "An internal error has occurred while trying to authenticate you. " + \
      "We received the error '%s' from slack. " % r.json()['error'] + \
      "Please try to authenticate again. "
    
  authed_user = r.json()['authed_user']
    
  users[authed_user['id']] = dict(type = "authed", token = authed_user['access_token'])
    
  return "You have authorized this app to post on your behalf! You can close this tab and go back to slack now."
  
helpjson = dict(response_type = "ephemeral", text = open("help.txt").read(), mrkdwn = True)
  
@app.route("/mathconf", methods = ["POST"])
def serve_mathconf():
  
  form = request.form
  
  inp = form['text'].strip().lower()
  uid = form['user_id']
  
  if inp == "help":
    return helpjson
  
  elif inp == "nopsst":
    user = users[uid]
    
    if user is None:
      users[uid] = dict(type = "nopsst")
      
      return dict(response_type = "ephemeral", text = "Success!")
    
    return dict(response_type = "ephemeral", text = "Already not nudging you!")
      
  elif inp == "revoke":
    user = users[uid]
    
    if user is None or user['type'] != 'authed':
      return dict(response_type = "ephemeral", text = "No auth token to revoke for this account!")
    
    r = revoke_token(user['token'])
    
    if not r.ok or not r.json()['ok']:
      return internal_error_json(r.json()['error'])
    
    del users[uid]
    
    return dict(response_type = "ephemeral", text = "Auth token removed successfully!")
  
  elif inp == "authorize":
    user = users[uid]
    
    if user is not None and user['type'] == 'authed':
      return dict(response_type = "ephemeral", text = "Already authed!")
    
    return dict(response_type = "ephemeral", text = "Use <%s|this link> to authenticate." % get_authorize_url(), mrkdwn = True)
  
  else:
    return dict(response_type = "ephemeral", text = "Invalid command! Please run '/mathconf help'.")