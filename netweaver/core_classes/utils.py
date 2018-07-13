def extrapolate_dict(numdict):
		newnumdict = {}
		if type(numdict) is not dict:
			raise TypeError
		for k, v in numdict.items():
			if type(k) is str:
				if '-' in k:
					nums = k.split('-')
					for n in range(int(nums[0]), int(nums[1]) + 1, 1):
						newnumdict.update({str(n): v})
				else:
					newnumdict.update({str(k): v})
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
		return newlist

def compare_dict_keys(d1, d2):
	for i in d1:
		if i not in d2:
			return False
	for i in d2:
		if i not in d1:
			return False
	return True