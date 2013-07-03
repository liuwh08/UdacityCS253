import os
import webapp2
import jinja2
from google.appengine.ext import db
import hmac
import re
import random
import string 
import hashlib
from register import User

SECRET = "I'm secret"


template_dir = os.path.join( os.path.dirname(__file__), 'templates')
jinja2_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def make_hash_str(key):
  return '%s|%s' %(key, hmac.new(SECRET, key).hexdigest())

def is_valid(hash_str):
  key = hash_str.split('|')[0]
  hsh = hash_str.split('|')[1]
  #print key, hsh
  if hmac.new(SECRET, key).hexdigest() == hsh:
    return key
  else:
    return None

def make_salt(length = 5):
  return ''.join(random.choice(string.letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
  if not salt:
    salt = make_salt()
  h = hashlib.sha256(name + pw + salt).hexdigest()
  return '%s|%s' %(salt, h)

def valid_pw(name, password, h):
  salt = h.split('|')[0]
  return h == make_pw_hash(name, password, salt)

class Handler(webapp2.RedirectHandler):
  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)

  def render_str(self, template, **params):
    t = jinja2_env.get_template(template)
    return t.render(params)

  def render(self, template, **kw):
    self.write(self.render_str(template, **kw))


class Register(Handler):
  def get(self):
    self.render("register.html")

  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    verify = self.request.get('verify')
    email = self.request.get('email')
    user_re = re.match(r'^[a-zA-Z0-9_-]{3,20}$', username)
    if not user_re:
      username_error = "That's not a valid username."
    else:
      username_error = ''
    if password != verify or password=='':
      passwd_error = 'That wasn\'t a valid password.'
    else:
      passwd_error = ''
    email_re = re.match(r'^[\S]+@[\S]+\.[\S]+$', email)
    if not email_re and email:
      email_error = "That's not a valid email"
    else:
      email_error = ''
    if username_error == '' and passwd_error == '' and email_error == '':
      u = User(username = username, password_hash = make_pw_hash(username, password), email = email)
      u.put()
      key = str(u.key().id())
      key_hash = make_hash_str(key)
      self.response.headers.add_header('Set-Cookie', "user_id=%s;Path=/" % key_hash) 
      #print "Redirecting.......\n"
      self.redirect('/wiki/')
    else:
      self.render('register.html', username = username, email = email, username_error = username_error, passwd_error = passwd_error, email_error = email_error)


class Login(Handler):
  def get(self):
    self.render('login.html')

  def post(self):
    Usr = db.Query(User)
    for u in Usr:
      print u.username
    username = self.request.get('username')
    password = self.request.get('password')
    print username, password
    Usr = db.Query(User).filter('username =', username).get()
    print Usr.username, Usr.password_hash
    if Usr and valid_pw(username, password, Usr.password_hash):
      key = str(Usr.key().id())
      key_hash = make_hash_str(key)
      self.response.headers.add_header('Set-Cookie', "user_id=%s;Path=/" % key_hash)
      self.redirect('/wiki/')
    else:
      self.render('login.html', username = username, login_error_msg = 'Invalid Username or Password!!')

class Logout(Handler):
  def get(self):
    self.response.headers.add_header('Set-Cookie','user_id=;access_token=deleted; Expires=Thu, 01-Jan-1970 00:00:00 GMT;Path=/')
    self.redirect('/wiki/')

def Wikikey(name = 'default'):
  return db.Key.from_path('Wikis', name)

class Wiki(db.Model):
  created = db.DateTimeProperty(auto_now_add = True)
  content = db.StringProperty(required = True)


def fetch_by_parent(Wikiname):
  q = Wiki.all().ancestor(Wikikey(Wikiname)).order('-created')
  return q

class WikiPage(Handler):
  def get(self, Wikiname):
    w = fetch_by_parent(Wikiname).get()
    if w:
      self.render('wiki.html', content = w.content)
    else:
      self.redirect('/wiki/_edit' + Wikiname)
        
class EditPage(Handler):
  def get(self, Wikiname):
    user_id_raw = self.request.cookies.get('user_id')
    if (not user_id_raw) or (not is_valid(user_id_raw)):
      self.response.headers.add_header('Set-Cookie','access_token=deleted; Expires=Thu, 01-Jan-1970 00:00:00 GMT;Path=/')
      self.redirect('/wiki/')
    w = fetch_by_parent(Wikiname).get()
    if w:
      content = w.content
    else:
      content = ''
    self.render('wiki_edit.html', content = content)

  def post(self, Wikiname):
    content = self.request.get('content')
    if content:
      w = Wiki(parent = Wikikey(Wikiname), content = content)
      w.put()
      self.redirect('/wiki' + Wikiname)
    else:
      error = "Content Please!!"
      self.render("wiki_edit.html", content = content, error = error)


    




PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
application = webapp2.WSGIApplication([('/wiki/signup', Register),
                                       ('/wiki/login', Login),
                                       ('/wiki/logout', Logout),
                                       ('/wiki/_edit'+PAGE_RE, EditPage),
                                       ('/wiki' + PAGE_RE, WikiPage),
                                       ], debug = True)

