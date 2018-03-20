import string 
import random
def gen(): 
    size = 20 
    allowed = string.ascii_letters 
    randomstring = ''.join([allowed[random.randint(0, len(allowed) - 1)] for x in xrange(size)]) 
    return randomstring  