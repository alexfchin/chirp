def rankSort(rank, items):
	if rank is "time":
		items = sorted(items, key=lambda item:item['timestamp']) #lambda is anon function, used in sorted method
	else: #sort by interest
		items = sorted(items, key=lambda item:item['property':{"likes"}]) #not sure if nested function is right
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