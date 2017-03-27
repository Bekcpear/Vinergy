#!/usr/bin/env python
# vim:fileencoding=utf-8

import os
from hashlib import md5
import time
import datetime

import bson
from tornado.web import RequestHandler, HTTPError, MissingArgumentError
import tornado.template

from . import model
from .util import util

def _create_template(self, name):
  '''don't compress_whitespace in <pre> incorrectly'''
  path = os.path.join(self.root, name)
  f = open(path, "rb")
  template = tornado.template.Template(
    f.read(), name=name, loader=self,
    compress_whitespace=False,
  )
  f.close()
  return template

tornado.template.Loader._create_template = _create_template

class BaseHandler(RequestHandler):
  def get_template_namespace(self):
    ns = super(BaseHandler, self).get_template_namespace()
    ns['url'] = self.request.full_url()
    ns['path'] = self.request.path
    return ns

class ShowCode(BaseHandler):
  def get(self, codeid):
    '''Browse code'''
    if codeid.rfind('/') != -1:
      # URL looks like wuitE/vim
      codeid, syntax = codeid.rsplit('/', 1)
    syntax = None
    doc = model.get_code_by_name(codeid)
    if not doc:
      raise HTTPError(404, codeid + ' not found')
    codes = dict(doc['content'])

    is_terminal = util.is_terminal(self.request.headers.get('User-Agent'))
    #self.set_header('Content-Type', 'text/plain')
    if is_terminal:
      # term
      r = util.render(code, 'TerminalFormatter', syntax)
      self.finish(r)
    else:
      # web
      r = util.render(codes['text'], 'HtmlFormatter', syntax)
      self.render('codeh.html', code=r)
      return

class Index(BaseHandler):
  def get(self):
    self.render('index.html')
    return

  def post(self):
    '''Insert new code'''
    try:
      code = self.get_argument('vimcn')
      # Content must be longer than "print 'Hello, world!'"
      # or smaller than 64 KiB
      if len(code) < 23 or len(code) > 64 * 1024:
        raise ValueError
      oid = bson.Binary(md5(code.encode('utf-8')).digest(),
                        bson.binary.MD5_SUBTYPE)
      r = model.get_codename_by_oid(oid)
      if r is not None:
        name = r
      else:
        name, count = util.name_count()
        # Python 3.3: datetime.datetime.utcnow().timestamp()
        epoch = time.mktime(datetime.datetime.utctimetuple(
          datetime.datetime.utcnow()))
        model.insert_code(oid, name, code, count, epoch)
      self.finish('%s://%s/t/%s\n' % (self.request.protocol, self.request.host, name))
    except MissingArgumentError:
      self.set_status(400)
      self.finish('Oops. Please Check your command.\n')
    except ValueError:
      self.set_status(400)
      tip = '''Hi, the code snippet must be longer than 'print("Hello, world!")' or shorter than 64 KiB.\n'''
      tip = util.render(tip, 'TerminalFormatter', 'py')
      self.finish(tip)

