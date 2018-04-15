from operator import itemgetter
def rankSort(rank, items):
    if rank is "time":
        items = sorted(items, key= lambda i: i['timestamp'], reverse=True) #lambda is anon function, used in sorted method
    else: #sort by interest
        items = sorted(items, key = lambda i: i['property']['likes'],reverse=True) #not sure if nested function is right
    return items
def noReplies(re, items):
    if re is not True:
        for item in items:
            if item['childType'] is "reply":
                items.remove(item)
    return items

def onlyMedia(m, items):
    if m is True:
        for item in items:
            if item['media'] is None:
                items.remove(item)
    return items