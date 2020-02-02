def cnt1():
    i = 0
    while True:
        i += 1
        yield i

def cnt1c():
    i = 0
    while True:
        i += 1
        yield (i, {str(i): i})

def cnt0(): 
    i = 0
    while True:
        yield i
        i = i + 1

