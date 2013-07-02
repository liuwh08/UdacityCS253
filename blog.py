#!/usr/bin/python 
# Problem Set 3 of CS253 Udacity

import os
import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import memcache
import time
import json
import logging

template_dir = os.path.join( os.path.dirname(__file__), 'templates')
jinja2_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RedirectHandler):
  def write(self, *a, **kw):
    self.response.out.write(*a, **kw)

  def render_str(self, template, **params):
    t = jinja2_env.get_template(template)
    return t.render(params)

  def render(self, template, **kw):
    self.write(self.render_str(template, **kw))
cache_time = {}
#cache_time['main'] = time.time()

def get_Main_Page(update = False):
  key = 'main'
  global cache_time
  posts = memcache.get(key)
  t = cache_time.get(key)
  #print update
  if posts is None or update or t is None:
    logging.error('DB Query') 
    posts = list(db.GqlQuery("select * from posts order by created desc limit 10"))
    memcache.set(key, posts)
    cache_time[key] = time.time()
  return posts

class MainPage(Handler):
  def get(self):
    posts = get_Main_Page()
    time_pass = time.time() - cache_time['main']
    self.render("front.html", posts = posts, time_pass = time_pass)

class NewBlog(Handler):
  def get(self):
    self.render("new_blog.html")

  def post(self):
    subject = self.request.get('subject')
    content = self.request.get('content')

    if subject and content:
      p = posts(subject = subject, content = content)
      p.put()
      memcache.delete('main')
      self.redirect('/blog/%s' % str(p.key().id()))
    else:
      error = "subject and content, please"
      self.render("new_blog.html", subject = subject, content = content, error = error)

def get_Post(key):
  global cache_time
  post = memcache.get(key)
  t = cache_time.get(key)
  print cache_time
  if post is None or t is None:
    logging.debug('DB single post query')
    k = db.Key.from_path('posts', int(key))
    post = db.get(k)
    memcache.set(key, post)
    cache_time[key] = time.time()
  return post

      

class ShowBlog(Handler):
  def get(self, key):
    global cache_time
    p = get_Post(key)
    print cache_time[key]
    self.render("blog.html", post = p, time_pass = time.time() - cache_time[key])

class posts(db.Model):
  subject = db.StringProperty(required = True)
  content = db.TextProperty(required = True)
  created = db.DateTimeProperty(auto_now_add = True)


class MainPageJson(Handler):
  def get(self):
    self.response.headers['Content-Type'] = 'application/json'
    posts = db.GqlQuery("select * from posts order by created desc limit 10")
    j = []
    for post in posts:
      content = post.content
      subject = post.subject
      created = post.created.strftime("%a, %d %b %Y %H:%M:%S")
      j.append({'content': content,
                'subject': subject,
                'created': created})
    j = json.dumps(j)
    self.write(j)

class SingleBlogJson(Handler):
  def get(self, key):
    self.response.headers['Content-Type'] = 'application/json'
    p = db.Key.from_path('posts', int(key))
    p = db.get(p)
    j = {'content': p.content,
         'subject': p.subject,
         'created': p.created.strftime("%a %d %b %Y %H:%M:%S")}
    j = json.dumps(j)
    self.write(j)

class Flush(Handler):
  def get(self):
    memcache.flush_all()
    cache_time.clear()
    self.redirect('/blog')




application = webapp2.WSGIApplication([
                                      (r'/blog/?', MainPage),
                                      (r'/blog/(\d+)', ShowBlog),
                                      (r'/blog/\.json', MainPageJson),
                                      (r'/blog/(\d+)\.json', SingleBlogJson),
                                      (r'/blog/flush/?', Flush),
                                      (r'/blog/newpost/?', NewBlog)], debug = True)

