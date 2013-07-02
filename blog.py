#!/usr/bin/python 
# Problem Set 3 of CS253 Udacity

import os
import webapp2
import jinja2
from google.appengine.ext import db
import time
import json

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

class MainPage(Handler):
  def get(self):
    posts = db.GqlQuery("select * from posts order by created desc limit 10")
    self.render("front.html", posts = posts)

class NewBlog(Handler):
  def get(self):
    self.render("new_blog.html")

  def post(self):
    subject = self.request.get('subject')
    content = self.request.get('content')

    if subject and content:
      p = posts(subject = subject, content = content)
      p.put()
      self.redirect('/blog/%s' % str(p.key().id()))
    else:
      error = "subject and content, please"
      self.render("new_blog.html", subject = subject, content = content, error = error)

      

class ShowBlog(Handler):
  def get(self, key):
    p = db.Key.from_path('posts', int(key))
    p = db.get(p)
    print p.subject, p.content
    
    self.render("blog.html", post = p)

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



application = webapp2.WSGIApplication([
                                      (r'/blog/?', MainPage),
                                      (r'/blog/(\d+)', ShowBlog),
                                      (r'/blog/\.json', MainPageJson),
                                      (r'/blog/(\d+)\.json', SingleBlogJson),
                                      (r'/blog/newpost/?', NewBlog)], debug = True)

