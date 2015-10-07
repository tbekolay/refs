import os
import sys

if sys.platform.startswith('win'):
    config_dir = os.path.expanduser(os.path.join("~", ".refs"))
else:
    config_dir = os.path.expanduser(os.path.join("~", ".config", "refs"))

install_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir))

rc = {'user': os.path.join(config_dir, "refsrc"),
      'project': os.path.abspath(os.path.join(os.curdir, "refsrc"))}
