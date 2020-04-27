import flask
from base64 import b64encode, b64decode

auth_url = 'https://slack.com/oauth/v2/authorize'
scopes = "chat:write"
client_id, client_secret = open("../oauth.txt", "r").read().splitlines()

def get_error_json(error):
  return {
    "text" : "Your latex couldn't be parsed.",
    "response_type" : "ephemeral",
    "blocks" : [{
      "type" : "section",
      "text" : {
        "type" : "plain_text",
        "text" : "Your latex couldn't be parsed. The error we received was '%s'." % error
      }
    }]
  }

def get_psst_json():
  return dict(
    text = 'Psst! I can do much more than just replying to your message.' + \
      ' If you give me permission, I can instead reply as you, making the chat much cleaner.' + \
      ' If this interests you, click ' + \
      '<{aurl}?client_id={cid}&user_scope={scopes}|here> to give me permission.'.format(aurl = auth_url, cid = client_id, scopes = scopes),
    mrkdwn = "true",
    response_type = "ephemeral"
  )

def get_success_json(inp):
  return {
    "text" : inp,
    "response_type" : "in_channel",
    "blocks" : [{
      "type": "image",
      "image_url": "https://slack-mathoid.kgugeler.ca/i/%s" % b64encode(inp.encode("utf-8")).decode("utf-8"), 
      "alt_text": inp
    }]
  }

def make_json_resp(json):
  return flask.Response(flask.json.dumps(json), mimetype = "application/json")