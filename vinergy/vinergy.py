#!/usr/bin/env python
# vim:fileencoding=utf-8

'''
vinergy.vinergy
~~~~~~~~~~~~~~~

Vinergy - CLI Pastebin within VimEnergy
'''

import os

import tornado.web
import tornado.ioloop
from tornado.options import define, options
from tornado.httpserver import HTTPServer

from . import handlers

### Templates
topdir = os.path.dirname(os.path.abspath(__file__))
tmpldir = os.path.join(topdir, 'templates')
staticdir = os.path.join(topdir, 'static')

### URL mappings
routers = (
  (r'/t', handlers.Index),
  (r'/t/(.*)', handlers.ShowCode),
)

def setup():
  from .config import PAD
  from .util import b52
  b52.PAD = PAD

def main():
  define("port", default=1718, help="run on the given port", type=int)
  define("address", default='', help="run on the given IP address", type=str)
  define("debug", default=False, help="debug mode", type=bool)

  tornado.options.parse_command_line()
  setup()
  application = tornado.web.Application(
    routers,
    gzip = True,
    debug = options.debug,
    template_path = tmpldir,
    static_path = staticdir,
  )
  http_server = HTTPServer(application, xheaders=True)
  http_server.listen(options.port, options.address)
  try:
    tornado.ioloop.IOLoop.instance().start()
  except KeyboardInterrupt:
    pass

if __name__ == "__main__":
  main()
