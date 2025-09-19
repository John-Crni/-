import copy
from operator import attrgetter
import inspect


class TEST:
    
    num1 = 0 #Last          1
    
    num2 = 0 #SnippingArea  2
    
    num3 = 0 #AnotherArea   3
    
    num4 = 0 #serialNumber  4
    
    def __init__(self,num1,num2,num3,num4):
        self.num1 = num1
        self.num2 = num2
        self.num3 = num3
        self.num4 = num4
        
    def P(self):
        print(self.num1 , "," , self.num2 , "," , self.num3, "," ,self.num4)
        
    def log(self):
        print(inspect.currentframe().f_code.co_name)
        
    def test(self):
        return 1,2,3

class LOG:
    
    def __init__(self):
        pass

    def test(self):
        t = TEST(1,1,1)
        t.log()

arry = [1,2]
one,two = arry

print(one)
t1 = TEST(1,1,1,2)
t1 = TEST(1,2,3,2)
t1 = TEST(1,2,2,2)
t1 = TEST(1,1,1,1)
t1 = TEST(1,2,3,1)
t1 = TEST(1,2,2,1)


arTEST = []
arTEST.append(t1)


arTEST.sort(key = attrgetter('num1','num3','num2'))
# arTEST.sort(key = attrgetter('num1','num3'))

for i in range(0,2):
    print(i)
