import requests

from base64 import b64encode

from flask import json

from threading import Lock

from time import time as now

class BearerAuth:
  def __init__(self, token):
    self.token = token
    
  def __call__(self, r):
    r.headers['Authorization'] = "Bearer " + self.token
    return r

class LockedDict:
  def __init__(self, val = {}):
    self.val = val
    self.lock = Lock()
    
  def __getitem__(self, key):
    with self.lock:
      return self.val.get(key)
    
  def __setitem__(self, key, v):
    with self.lock:
      self.val[key] = v
      
  def __delitem__(self, key):
    with self.lock:
      del self.val[key]
      
CACHE_TIMEOUT = 60 # 1 minute

class LockedCache(LockedDict):
  def __getitem__(self, key):
    with self.lock:
      if key not in self.val: return None
    
      return self.val[key]['img']
  
  def __setitem__(self, key, v):
    with self.lock:
      curtime = now()
      
      keys = [k for k in self.val if curtime - self.val[k]['time'] > CACHE_TIMEOUT]
      
      for k in keys:
        del self.val[k]
    
      self.val[key] = dict(img = v, time = now())

# LockedDict but the dict is backed by a JSON file
class LockedJSON(LockedDict):
  def __init__(self, filename):
    self.filename = filename
    super().__init__(json.load(open(filename)))
  
  def __setitem__(self, key, v):
    with self.lock:
      self.val[key] = v
      
      with open(self.filename, "w") as f:
        f.write(json.dumps(self.val))
        
  def __delitem__(self, key):
    with self.lock:
      del self.val[key]
      
      with open(self.filename, "w") as f:
        f.write(json.dumps(self.val))
        
def latexify(texstr):
  # Mathoid server
  r = requests.post("http://localhost:10044/png", data = dict(q = texstr))
  
  if r.status_code == 400:
    raise RuntimeError(r.json()['error'])
    
  return r.content

img_cache = LockedCache()

users = LockedJSON("../users.json")