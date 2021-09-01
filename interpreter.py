

import re
import datetime
from typing import SupportsBytes

def givenPattern(pat) :
	def wrapped(string) :
		return pat.match(string)
	return wrapped

def givenRegx(reg) :
	def wrapped(string) :
		res = reg.search(string)
		if res == None :
			return ((0, 0), None)
		return (res.span(), res.group())
	return wrapped

# We define any pattern as several parallel possible sub_pattern sequence:
# pattern = [[sub1, sub2, sub3], [sub1, sub2, sub3]]
# when a pattern matches a string, if and only if, one of the sequence is matched

class Pattern :

	def __init__(self) :

		self.subPatterns = []
		self.subResults = []
		self.combiners = []
		
	# I used wrapper to view patterns and regxprs the same way
	# pattern(string) = ((l,r), (res1, res2, ...))
	def appendSubPatternSeq(self, subpattern, combiner) :

		wrappedSubPattern = []
		for item in subpattern :
			if type(item) == Pattern :
				wrappedSubPattern.append(givenPattern(item))
			else :
				item = re.compile(item)
				wrappedSubPattern.append(givenRegx(item))
		self.subPatterns.append(wrappedSubPattern)
		self.combiners.append(combiner)
	
	# match trys every possible pattern sequence to match the given string
	# when one is fit, just return
	def match(self, string) :	# can search on <Pattern> or <re.Match_Object>
		
		for sequence,combiner in zip(self.subPatterns,self.combiners) :
			curStr = string
			curRes = []
			curLen = 0
			for sub in sequence :
				res = sub(curStr)
				if res == None :
					break
				curRes.append(res[1])
				curLen += res[0][1]
				curStr = curStr[res[0][1]:]
			else :
				curSum = combiner(*curRes)
				if curSum != None :
					return ((0, curLen), curSum)
		return None

# TextInterpreter can interpret a string
# pattern and functions are given to the interpreter in pairs
# when only one pattern matches the given string
# the interpreter calls the correspoding function
class TextInterpreter :

	# when there are 0 or more than 1 matches
	# call function whenNone and whenMultiple 
	def __init__(self) :

		self.patternFuncSeq = []
		self.whenNone = None
		self.whenMultiple = None
		pass

	def registerNoneFunction(self, func) :

		self.whenNone = func

	def registerMultipleFunction(self, func) :

		self.whenMultiple = func

	def appendPattern(self, pat, recall) :

		self.patternFuncSeq.append((pat, recall))
	
	# doing interpretation and calling corresponding functions
	def doInterprete(self, string) :

		successNum = 0
		funcParaPair = None
		for pattern,func in self.patternFuncSeq :
			tmp = pattern.match(string)
			if tmp != None :
				_,res = tmp
				funcParaPair = (func, res)
				successNum += 1
		if successNum == 0 :
			if self.whenNone != None :
				return self.whenNone()
			else :
				return "No interpretation found!"
		elif successNum >= 2 :
			if self.whenMultiple != None :
				return self.whenMultiple()
			else :
				return "Multiple interpretation found!"
		else :
			return funcParaPair[0](*funcParaPair[1])

pReserve = Pattern()
pQuery = Pattern()
pIam = Pattern()
pTime = Pattern()
pDate = Pattern()
pClock = Pattern()
pNumber = Pattern()
pNumber_adj = Pattern()	# numbers that have no preceeding letters
pLocation = Pattern()

def initPatterns() :

	def chineseNumber(s) :
		return '零一二三四五六七八九十'.index(s)
	
	def readChinese(s) :
		
		if len(s)==1 and s[0] in ['日','天'] :
			return 7
		elif s.isdigit() :
			return int(s)
		else :#是中文
			ret = 0
			t = [chineseNumber(x) for x in s]
			if len(t) == 1 :
				return t[0]
			elif len(t) == 2 :
				if t[0] == 10 :
					return t[1]+10
				else :
					assert(t[1] == 10)
					return t[0]*10
			else :
				assert(len(t) == 2)
				assert(t[1] == 10)
				return t[0]*10 + t[2]

	def nextMonday() :
		for i in range(10) :
			day = datetime.date.today() + datetime.timedelta(days=i)
			if day.weekday() == 0 :
				return day
		raise "No next monday found!!!"
	
	def haveNone(*arg) :
		for a in arg :
			if a==None :
				return True
		return False

	# Defining numbers
	pNumber.appendSubPatternSeq(
		[r'[零一二三四五六七八九十0-9日天]+'],
		lambda x : None if x==None else (readChinese(x),)
	)
	pNumber_adj.appendSubPatternSeq(
		[r'^[零一二三四五六七八九十0-9日天]+'],
		lambda x : None if x==None else (readChinese(x),)
	)

	# Defining date
	pDate.appendSubPatternSeq(
		[r'今天'],
		lambda x : None if x==None else (datetime.date.today(),)
	)
	pDate.appendSubPatternSeq(
		[r'明天'],
		lambda x : None if x==None else (datetime.date.today() + datetime.timedelta(days=1),)
	)
	pDate.appendSubPatternSeq(
		[r'大*后天'],
		lambda x : None if x==None else (datetime.date.today() + datetime.timedelta(days=1)*len(x),)
	)
	pDate.appendSubPatternSeq(
		[r'大*后天'],
		lambda x : None if x==None else (datetime.date.today() + datetime.timedelta(days=1)*len(x),)
	)
	pDate.appendSubPatternSeq(
		[r'下*个?(周|星期)', pNumber_adj],
		lambda x,y : None if haveNone(x,y) else (nextMonday() + datetime.timedelta(days=y[0]+x.count('下')*7-8),)
	)
	pDate.appendSubPatternSeq(
		[pNumber, r'月', pNumber_adj, r'日*|号*'],
		lambda x,_1,y,_2 : None if haveNone(x,_1,y,_2) else (datetime.date.today().replace(month=x[0], day=y[0]),)
	)
	pDate.appendSubPatternSeq(
		[pNumber, r'\.', pNumber_adj, r'\.', pNumber_adj, r'[ ]|$'],
		lambda x,_1,y,_2,z,_3 : None if haveNone(x,_1,y,_2,z,_3) else (datetime.date.today().replace(year=x[0], month=y[0], day=z[0]),)
	)
	pDate.appendSubPatternSeq(
		[pNumber, r'\.', pNumber_adj, r'[ ]|$'],
		lambda x,_1,y,_2 : None if haveNone(x,_1,y,_2) else (datetime.date.today().replace(month=x[0], day=y[0]),)
	)

	# Defining clock
	pClock.appendSubPatternSeq(
		[r'上午|早', pNumber, r'\:|点', pNumber_adj],
		lambda x,y,_,z : None if haveNone(x,y,_,z) else (datetime.datetime.strptime(str(y[0])+':'+str(z[0])+' AM', '%I:%M %p').time(),)
	)
	pClock.appendSubPatternSeq(
		[r'下午|晚', pNumber, r'\:|点', pNumber_adj],
		lambda x,y,_,z : None if haveNone(x,y,_,z) else (datetime.datetime.strptime(str(y[0])+':'+str(z[0])+' PM', '%I:%M %p').time(),)
	)
	pClock.appendSubPatternSeq(
		[pNumber, r'\:', pNumber_adj, r'am|pm|AM|PM|Am|Pm'],
		lambda x,_,y,z : None if haveNone(x,_,y,z) else (datetime.datetime.strptime(str(x[0])+':'+str(y[0])+' '+z, '%I:%M %p').time(), )
	)
	pClock.appendSubPatternSeq(
		[pNumber, r'\:', pNumber_adj],
		lambda y,_,z : None if haveNone(y,_,z) else (datetime.datetime.strptime(str(y[0])+':'+str(z[0]), '%H:%M').time(),)
	)
	pClock.appendSubPatternSeq(
		[r'上午|早', pNumber, r'^点半'],
		lambda x,y,z : None if haveNone(x,y,z) else (datetime.datetime.strptime(str(y[0])+':'+str(30)+' AM', '%I:%M %p').time(), )
	)
	pClock.appendSubPatternSeq(
		[r'上午|早', pNumber, r'^点'],
		lambda x,y,_ : None if haveNone(x,y,_) else (datetime.datetime.strptime(str(y[0])+':'+str(0)+' AM', '%I:%M %p').time(), )
	)
	pClock.appendSubPatternSeq(
		[r'下午|晚', pNumber, r'^点半'],
		lambda x,y,z : None if haveNone(x,y,z) else (datetime.datetime.strptime(str(y[0])+':'+str(30)+' PM', '%I:%M %p').time(), )
	)
	pClock.appendSubPatternSeq(
		[r'下午|晚', pNumber, r'^点'],
		lambda x,y,_ : None if haveNone(x,y,_) else (datetime.datetime.strptime(str(y[0])+':'+str(0)+' PM', '%I:%M %p').time(), )
	)
	pClock.appendSubPatternSeq(
		[pNumber_adj, r'^点半'],
		lambda x,_ : None if haveNone(x,_) else (datetime.datetime.strptime(str(x[0])+':'+str(30), '%H:%M').time(), )
	)
	pClock.appendSubPatternSeq(
		[pNumber_adj, r'^点'],
		lambda x,_ : None if haveNone(x,_) else (datetime.datetime.strptime(str(x[0])+':'+str(0), '%H:%M').time(), )
	)

	# Defining location
	pLocation.appendSubPatternSeq(
		[r'B|b', pNumber_adj],
		lambda x,y : None if haveNone(x,y) else ('B'+str(y[0]),)
	)
	pLocation.appendSubPatternSeq(
		[pNumber],
		lambda x : None if x==None else ('B'+str(x[0]),)
	)

	# Defining time
	# time = begin to end
	pTime.appendSubPatternSeq(
		[pDate, pClock, r'到|至', pClock],
		lambda x,y,_,z : None if haveNone(x,y,_,z) else (datetime.datetime.combine(x[0],y[0]), datetime.datetime.combine(x[0],z[0]))
	)

	# Defining reserve
	# reserve = when and where
	pReserve.appendSubPatternSeq(
		['^预约', pTime, pLocation],
		lambda x,y,z : None if haveNone(x,y,z) else (*y, *z)
	)
	pReserve.appendSubPatternSeq(
		['^预约', pTime],
		lambda x,y : None if haveNone(x,y) else (*y, None)
	)

	# Defining Query
	# query = when and where
	pQuery.appendSubPatternSeq(
		['^查询', pTime, pLocation],
		lambda x,y,z : None if haveNone(x,y,z) else (*y, *z)
	)
	pQuery.appendSubPatternSeq(
		['^查询', pTime],
		lambda x,y : None if haveNone(x,y) else (*y, None)
	)
	pQuery.appendSubPatternSeq(
		['^查询', pDate, pLocation],
		lambda x,y,z : None if haveNone(x,y,z) else (y[0], y[0]+datetime.timedelta(days=1), *z)
	)
	pQuery.appendSubPatternSeq(
		['^查询', pDate],
		lambda x,y : None if haveNone(x,y) else (y[0], y[0]+datetime.timedelta(days=1), None)
	)
	pQuery.appendSubPatternSeq(
		['^查询', pLocation],
		lambda x,y : None if haveNone(x,y) else (None, None, *y)
	)
	pQuery.appendSubPatternSeq(
		['^查询'],
		lambda x : None if x==None else (None, None, None)
	)

	# Defining I am
	pIam.appendSubPatternSeq(
		['^我是', '.*'],
		lambda x,y : None if haveNone(x,y) else (y,)
	)

	print('下面一长串时测试代码，如果其中有一个为None请小心')
	print(pDate.match('大后天'))
	print(pNumber.match('1982'))
	print(pNumber.match('三十'))
	print(pDate.match('下个周日'))
	print(pDate.match('星期一'))
	print(pDate.match('9月8号'))
	print(pDate.match('2010.9.9'))
	print(pDate.match('12.2'))
	print(pClock.match('下午九点三十'))
	print(pClock.match('19:30'))
	print(pClock.match('早上8:00'))
	print(pClock.match('6:30pm'))
	print(pClock.match('早上八点半'))
	print(pClock.match('晚八点'))
	print(pTime.match('今天早上八点到晚上八点'))
	print(pLocation.match('252'))
	print(pLocation.match('B252'))
	print(pReserve.match('预约2021.9.1 8:40am到晚上七点半的B252'))
	print(pReserve.match('预约明天上午8:00到九点半'))
	print(pQuery.match('查询'))
	print(pQuery.match('查询252'))
	print(pQuery.match('查询明天'))
	print(pQuery.match('查询2020.6.4 252'))
	print(pIam.match('我是李云迪'))
	pass

if __name__ == '__main__' :

	initPatterns()

	'''
	def m1(para) :
		print("pattern1 matched!")
		print(para)
	
	def m2(para) :
		print("pattern2 matched!")
		print(para)
	
	inter = TextInterpreter()
	
	pat1 = Pattern()
	pat1.appendSubPatternSeq([r'[0-9]+', r'\+', r'[0-9]+'], lambda a,b,c:None if a==None or b==None else (int(a)+int(c),))
	inter.appendPattern(pat1, m1)
	inter.doInterprete(input())
	'''
	pass