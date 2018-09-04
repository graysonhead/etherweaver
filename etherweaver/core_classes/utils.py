import collections.abc
import copy


def extrapolate_dict(numdict, int_key=False):
		newnumdict = {}
		if type(numdict) is not dict:
			raise TypeError
		for k, v in numdict.items():
			if type(k) is str:
				if '-' in k:
					nums = k.split('-')
					for n in range(int(nums[0]), int(nums[1]) + 1, 1):
						if int_key:
							newnumdict.update({int(n): v})
						else:
							newnumdict.update({str(n): v})
				else:
					if int_key:
						newnumdict.update({int(k): v})
					else:
						newnumdict.update({str(k): v})
			else:
				if int_key:
					newnumdict.update({int(k): v})
				else:
					newnumdict.update({str(k): v})
		return newnumdict


def extrapolate_list(numlist, int_out=False):
		newlist = []
		if type(numlist) is not list:
			raise TypeError
		for num in numlist:
			if type(num) is str:
				if '-' in num:
					nums = num.split('-')
					for n in range(int(nums[0]), int(nums[1]) + 1, 1):
						newlist.append(str(n))
				else:
					newlist.append(str(num))
			else:
				newlist.append(str(num))
		if int_out:
			intlist = []
			for num in newlist:
				intlist.append(int(num))
			return intlist
		else:
			return newlist


def compare_dict_keys(d1, d2):
	for i in d1:
		if i not in d2:
			return False
	for i in d2:
		if i not in d1:
			return False
	return True


def smart_dict_merge(d, u, in_place=False):
	if in_place:
		for k, v in u.items():
			if isinstance(v, collections.abc.Mapping, in_place=in_place):
				d[k] = smart_dict_merge(d.get(k, {}), v)
			else:
				d[k] = v
		return d
	else:
		dn = copy.deepcopy(d)
		for k, v in u.items():
			if isinstance(v, collections.abc.Mapping):
				dn[k] = smart_dict_merge(dn.get(k, {}), v, in_place=in_place)
			else:
				dn[k] = v
		return dn


def compact_list(uncompacted_list, single_item_out=str):
	"""
	This takes a list like [1, 2, 3, 5, 7] and turns it into ['1-3', 5, 7]
	:param uncompacted_list:
	:return:
	"""
	new_list = []
	startrange = None
	for i in range(0, uncompacted_list.__len__()):
		# Make sure we aren't going to overrun the index of the list
		if i + 1 < uncompacted_list.__len__():
			if uncompacted_list[i] + 1 == uncompacted_list[i + 1]:
				if startrange == None:
					startrange = uncompacted_list[i]
				else:
					pass
			else:
				if startrange:
					new_list.append('{}-{}'.format(str(startrange), uncompacted_list[i]))
					startrange = None
				else:
					if single_item_out == str:
						new_list.append(str(uncompacted_list[i]))
					if single_item_out == int:
						new_list.append(uncompacted_list[i])
		# This is the last item in the list
		else:
			# If startrange isn't none, then we were iterating through contigous numbers
			if startrange:
				new_list.append('{}-{}'.format(str(startrange), uncompacted_list[i]))
				startrange = None
			else:
				if single_item_out == str:
					new_list.append(str(uncompacted_list[i]))
				if single_item_out == int:
					new_list.append(uncompacted_list[i])
	return new_list