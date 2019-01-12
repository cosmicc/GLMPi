import subprocess

a = subprocess.check_output(['vcgencmd', 'get_throttled'])
a = a.split(b'=')
print( a[1].decode('UTF-8').strip() )

