# Reference: http://hexo.tanglei.name/blog/aprioriall-algorithm-in-python.html
# Reference: https://blog.csdn.net/tszw1007/article/details/77871133
import copy
import math
import re

def getSubSets(items, remove_origin=False):
    # the power set of the empty set has one element, the empty set
    result = [[]]
    for x in items:
        result.extend([subset + [x] for subset in result])
    if(remove_origin):
        result.pop()
        result.remove([])
    return result

class Basket():
    items=[]#Apple,orange,....
    def __init__(self,items):
        self.items = items
    def setItems(self,items):
        self.items = items
    def __str__(self):
        mystr='Basket[ '
        for i in self.items:
            mystr = mystr + i +' , '
        mystr += ']'
        return mystr
            
class Custom():
    baskets=[]#basket1,basket2
    mapNums=set()#maped num
    def __init__(self,baskets):
        self.baskets = baskets
    def setBaskets(self,baskets):
        self.baskets = baskets
    def setMapedNums(self,mapNums):
        self.mapNums = mapNums
    def  __str__(self):
        mystr='Custom[ '
        for i in self.baskets:
            mystr = mystr + i.__str__() +' , '
        mystr += ']'
        return mystr
    def getMapedNums(self):
        return self.mapNums
        
class AprioriAll():
    customs=[]
    minSuppCount = 0#count  number ,considering the min_supp and the num of transactions
    allBaskets=[]
    transMap={}
    def __init__(self,min_supp=0.4,datafile='aprioriall.txt'):
        inputfile = open(datafile,"r")
        self.min_supp = min_supp
        baskets=[]
        self.customs=[]
        for line in inputfile.readlines():
            if(line != "\n"):
                items = re.compile(r"\w+").findall(line)
                basket = Basket(items)
                baskets.append(basket)
            else:
                custom = Custom((baskets))
                self.customs.append(custom)
                baskets=[] 
        #add the last custom         
        custom = Custom((baskets))
        self.customs.append(custom)
        
        self.minSuppCount = math.ceil(min_supp * len(self.customs))
        
    def sortPhase(self):
        '''sort the transaction db :with  customer-id as the major key and 
        transaction-time as the minor key. '''
        #has been done in the constructor
        pass
    
    def litemsetPhase(self):
        ''' find all the fequent-itemsets whose support is above the threshold'''
        litemset = []
        items = []
        allBaskets = []
        for custom in self.customs:
            for basket in custom.baskets:
                allBaskets.append(basket)
                for item in basket.items:
                    if [item] not in items:
                        items.append([item])
                    
        items.sort()
        
        #remove who blow the threshold
        candidates=items
        while True:
            temp=[]
            for item1 in candidates:
                count = 0
                for basket in allBaskets:
                    set1 = set(item1)
                    if set1.issubset(basket.items):
                        count += 1
                if count >= self.minSuppCount:
                    print("Frequent %d-itemset : %s" %(len(item1),item1))
                    temp.append(item1)
                    litemset.append(item1)
            
            candidates = self.__genCandidate(temp)
            if len(candidates) == 0 :
                break
        self.allBaskets = allBaskets
        return litemset
    
    def transformationPhase(self,transmap):
        for custom in self.customs:
            mapNums=set()#store the maped numbers of each custom
            for basket in custom.baskets:
                for k in transmap.keys():
                    s1 = set(transmap[k])
                    s2 = set(basket.items)
                    if s1.issubset(s2):
                        mapNums.add(k)
            custom.setMapedNums(mapNums)   
            
    def sequencePhase(self,mapNums):
        
        item1set = set()#
        for num in mapNums :
            item1set=item1set.union(num)
                      
        item1list=list(item1set)
        item1list.sort()
        
        seqresult=[]
        candidates=[]
        for item in item1list:
            candidates.append([item])
        while True:
            for item in candidates:
                count = 0 
                for seq in mapNums:
                    s1 = set(item)
                    if s1.issubset(seq):
                        count += 1
                if count >= self.minSuppCount:
                    print("Frequent %-itemsets : %s" %(len(item),item))
                    seqresult.append(item)       
            candidates = self.__genCandidate(candidates) 
            if len(candidates) == 0 :
                break
        return seqresult
    def maxSeq(self,seqs):
        maxSeq=copy.deepcopy(seqs)
        for seq in seqs:
            t_set = set(seq)
            for seq1 in seqs:
                t_set1 = set(seq1)
                if t_set1 != t_set and t_set1.issuperset(t_set):
                    maxSeq.remove(seq)
                    break
        return self.__map2seq(maxSeq)          
    def createTransMap(self,litemset):
        transmap = {}
        value = 1
        for each in litemset:
            transmap[value]=each
            value += 1
        self.transMap = transmap
        return transmap
    
    def __map2seq(self,seqs):
        #transform numseq to original seq
        origSeqs = []
        for seq in seqs:
            origSeq=[]
            for item in seq:    
                origSeq.append(self.transMap[item])
            origSeqs.append(origSeq)
        return origSeqs    
    def __genCandidate(self,frequentItems):    
        #gen new canidate
        length = len(frequentItems) 
        result = []#add one item   
        for i in range(length):
            for j in range(i+1,length):
                if self.__lastDiff(frequentItems[i],frequentItems[j]):
                    item = copy.deepcopy(frequentItems[i])
                    item.insert(len(frequentItems[i]),frequentItems[j][len(frequentItems[j])-1])
                    if False == self.__has_inFrequentItemsets(frequentItems, item):
                        result.append(item)
        return result
    #check if there is none subsets of item in the frequentItems 
    def __has_inFrequentItemsets(self,frequentItems,item):
        subs = getSubSets(item,remove_origin=True)
        for each in subs:
            if(each == []):
                continue
            flag=False
            for i in frequentItems:
                if i == each:
                    flag=True
                    break 
            if flag==False:
                return True  
        return False #there is at least one subset in the freq-items
        
    def __lastDiff(self,items1,items2):
        if len(items2) != len(items1):#length should be the same
            return False
        if items1 == items2:#if all the same,return false
            return False
        return items1[:-1] == items2[:-1]    


if __name__ == '__main__':
    aa = AprioriAll(min_supp=0.4,datafile='aprioriall2.txt')
    litemset = aa.litemsetPhase()
    print("litemset:");print(litemset)
    transmap = aa.createTransMap(litemset);
    print("transformation map :");print(transmap)
    aa.transformationPhase(transmap)
    customs = aa.customs
    mapNums = []
    for each in customs:
        mapNums.append(each.getMapedNums())
    seqNums = aa.sequencePhase(mapNums)
    maxSeqs= aa.maxSeq(seqNums)
    print("The sequential patterns :");print(maxSeqs)