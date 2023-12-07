# From http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/213761
# Python compatibility:
from __future__ import absolute_import

# Standard library:
import random
import time
from hashlib import md5


def uuid( *args ):
  """
    Generates a universally unique ID.
    Any arguments only create more randomness.
  """
  t = int( time.time() * 1000 )
  r = int( random.random() * 100000000000000000 )
  try:
    a = socket.gethostbyname( socket.gethostname() )
  except:
    # if we can't get a network address, just imagine one
    a = random.random() * 100000000000000000
  data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
  if not isinstance(data, bytes):
      data = data.encode('ascii')
  data = md5(data).hexdigest()
  return data


if __name__ == '__main__':
    print(uuid())
