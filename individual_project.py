import matplotlib.pyplot as plt
from pymining import itemmining, assocrules
from aprioriall import *
import numpy as np

# ======== Parameter Part (you can set) ======== #
ARM_MIN_SUPPORT = 500
DATASCALE_LIMIT = 300 # -1 for INF
CLUSTER_MIN_PRINT_SIZE = 10
CLUSTER_THRESHOLD = 0.4
N_OF_CLUSTERS = 150
DEFAULT_MODE = "groupavg" # "groupavg" or "complete" for clustering
PREPROCESSING = False # For removing users with one visiting page


user_dict = []
page_list = [-1]*1500
data_list = []
n_users = 0
n_pages = 0

dis_matrix = 0
dis_values = []

def readfile(filename):
    global n_pages, n_users
    file = open(filename, "r")
    user_id = -1
    cur_user_count = 0
    for line in file.readlines():
        line = line.replace("\"","")
        line_list = line.split(",")
        if(line_list[0]=='A'):
            n_pages += 1
            index = int(line_list[1])
            page_list[index] = line_list[3]
        if(line_list[0]=='C'):
            if(DATASCALE_LIMIT!=-1 and n_users>=DATASCALE_LIMIT):
                break
            if(PREPROCESSING and cur_user_count==1):
                user_dict.pop()
                data_list.pop()
                n_users -= 1
            cur_user_count = 0
            user_id = n_users
            user_dict.append(int(line_list[2]))
            data_list.append([])
            n_users += 1
        if(line_list[0]=='V'):
            cur_user_count += 1
            item = int(line_list[1])
            data_list[user_id].append(item)
    print("Done! User =",n_users,", Pages =",n_pages)
    file.close()

# ==== ARM ====
def ARM(print_table = False):
    visits = data_list
    relim_input = itemmining.get_relim_input(visits)
    report = itemmining.relim(relim_input, ARM_MIN_SUPPORT)
    print("====REPORT====")
    if(print_table):
        print("* Top frequent visited pages *")
        for itemset in report.keys():
            if(len(itemset)==1):
                t=next(iter(itemset))
                print(t, report[itemset], page_list[t], sep='\t')
    else:
        print("Total number frequent itemsets:",len(report))
        print(report)
    rules1 = assocrules.mine_assoc_rules(report, min_support=ARM_MIN_SUPPORT, min_confidence=0.5)
    print("====RULE====")
    for line in rules1:
        if (len(line[0])+len(line[1])>=4):
            #print(line)
            print("{",end='')
            for i in line[0]:
                print(str(i)+": "+str(page_list[i])+", ",end='')
            print("}",end=' => ')
            print("{",end='')
            for i in line[1]:
                print(str(i)+": "+str(page_list[i])+", ",end='')
            print("}",end=', ')
            print("Sup=",line[2],sep='',end=', ')
            print("Conf=",line[3],sep='')


# ==== Sequential ARM ====
def generate_aprioriall_data(filename):
    wfile = open(filename, "w")
    assert n_users == len(data_list)
    for i in range(n_users):
        for item in data_list[i]:
            print(item, file = wfile)
        print("", file = wfile)
    wfile.close()

def flat(nums):
    res = []
    for i in nums:
        if isinstance(i, list):
            res.extend(flat(i))
        else:
            res.append(i)
    return res

def sequentialARM(input_filename, min_seq_len=2):
    aa = AprioriAll(min_supp=0.02,datafile=input_filename)
    litemset = aa.litemsetPhase()
    print("litemset:")
    print(litemset)
    transmap = aa.createTransMap(litemset)
    print("transformation map :")
    print(transmap)
    aa.transformationPhase(transmap)
    customs = aa.customs
    mapNums = []
    for each in customs:
        mapNums.append(each.getMapedNums())
    seqNums = aa.sequencePhase(mapNums)
    maxSeqs= aa.maxSeq(seqNums)
    print("The sequential patterns :")
    #print(maxSeqs)
    for i in maxSeqs:
        if(len(i)>=min_seq_len):
            for j in flat(i):
                print(j+": "+page_list[int(j)]+", ",end='')
            print("")


# ==== User Clustering ====
def cal_distance(set1, set2):
    set1 = set(set1)
    set2 = set(set2)
    return 1-len(set1&set2)/len(set1|set2)

def cal_dis_matrix():
    print("Now calculating distance matrix ...")
    global dis_matrix, dis_values
    dis_values = []
    dis_matrix = np.zeros([n_users,n_users], dtype=np.float)
    for i in range(n_users):
        if(i%100==0):
            print(i,"...",end=" ")
        for j in range(n_users):
            dis_matrix[i,j]=cal_distance(data_list[i],data_list[j])
            dis_matrix[j,i]=dis_matrix[i,j]
            dis_values.append(dis_matrix[i,j])
    print("Distance Matrix Calculated!")
    dis_values.sort()
    print("Distance Matrix Sorted!")
    print("0%=",dis_values[0],", 25%=",dis_values[int(len(dis_values)*0.25)],", 50%=",dis_values[int(len(dis_values)*0.5)],", 75%=",dis_values[int(len(dis_values)*0.75)],", 100%=",dis_values[-1],sep='')

def linkage_distance(set1, set2, mode=DEFAULT_MODE):
    dis = -1
    if(mode=="complete"):
        dis = -1
        for i in set1:
            for j in set2:
                if(dis_matrix[i,j]>dis):
                    dis = dis_matrix[i,j]
    if(mode=="groupavg"):
        dis = 0
        for i in set1:
            for j in set2:
                dis += dis_matrix[i,j]
        dis = dis/(len(set1)*len(set2))
    return dis

def detect_centroid(userset):
    global data_list
    min_sum_dis = -1
    centroid_id = -1
    for i in userset:
        t_dis = 0
        for j in userset:
            if(i==j):
                continue
            t_dis += cal_distance(data_list[i], data_list[j])
        if(t_dis<min_sum_dis or min_sum_dis==-1):
            min_sum_dis = t_dis
            centroid_id = i
    return centroid_id

        
def clustering_users_with_threshold(threshold = CLUSTER_THRESHOLD):
    #AGNES
    cal_dis_matrix()
    sset = []
    #min_dis_list = []
    #min_dis = 100
    for i in range(n_users):
        sset.append([i])
    flag = True
    t=0
    print("Begin combining...")
    while(flag):
        flag = False
        # Combine n-number_of_clusters times
        n_sets = len(sset)
        #min_dis = 100
        combine_1 = -1
        combine_2 = -1
        for i in range(n_sets-1):
            for j in range(i+1, n_sets):
                t_dis = linkage_distance(sset[i], sset[j])
                if(t_dis < threshold):
                    combine_1 = i
                    combine_2 = j
                    flag=True
                    break
            if(flag):
                break
        sset[combine_1]=sset[combine_1]+sset[combine_2]
        sset.remove(sset[combine_2])
        t+=1
        if(t%50==0):
            print(t,end="...")
    print("")
    print("Total number of clusters:",n_users-t)
    for s in sset:
        if(len(s)>CLUSTER_MIN_PRINT_SIZE):
            centroid = detect_centroid(s)
            print("\nCluster centroid:",user_dict[centroid],"Cluster size:",len(s))
            for i in data_list[centroid]:
                print(i,": ",page_list[i],end=', ',sep='')


def clustering_users(n_of_clusters=N_OF_CLUSTERS):
    #AGNES
    cal_dis_matrix()
    sset = []
    min_dis_list = []
    min_dis = 100
    for i in range(n_users):
        sset.append([i])
    for t in range(n_users-n_of_clusters):
        # Combine n-number_of_clusters times
        n_sets = len(sset)
        min_dis = 100
        combine_1 = -1
        combine_2 = -1
        for i in range(n_sets-1):
            for j in range(i+1, n_sets):
                t_dis = linkage_distance(sset[i], sset[j])
                if(t_dis < min_dis):
                    combine_1 = i
                    combine_2 = j
                    min_dis = t_dis
        sset[combine_1]=sset[combine_1]+sset[combine_2]
        sset.remove(sset[combine_2])
        min_dis_list.append(min_dis)
        if(t%50==0):
            print(t,end="...")
    print("")
    print("Total number of clusters:",n_users-t-1)
    #print(min_dis_list)
    plt.plot(min_dis_list)
    plt.show()
    '''
    for i in min_dis_list:
        print(round(i,2),end=", ")
    '''
    print("")
    for s in sset:
        if(len(s)>CLUSTER_MIN_PRINT_SIZE):
            centroid = detect_centroid(s)
            print("\nCluster centroid:",user_dict[centroid],"Cluster size:",len(s))
            for i in data_list[centroid]:
                print(i,": ",page_list[i],end=', ',sep='')


# ======== Running Part (comment the function you don't need) ======== #
# readfile: compulsory data reading and processing function
readfile("C:/Users/54611/OneDrive/Subject Files/COMP4433 Data Mining and Data Warehousing/Individual/anonymous-msweb/anonymous-msweb.data")

# --- ARM: for association rule mining
ARM()

# --- generate_aprioriall_data: compulsory for AprioriAll method
# --- sequentialARM: call AprioriAll for sequential ARM
generate_aprioriall_data("C:/Users/54611/OneDrive/Subject Files/COMP4433 Data Mining and Data Warehousing/Individual/anonymous-msweb/aprioriall_input.txt")
sequentialARM("C:/Users/54611/OneDrive/Subject Files/COMP4433 Data Mining and Data Warehousing/Individual/anonymous-msweb/aprioriall_input.txt")

# --- clustering_users: clustering method (time and space complexity is too high for 30000+ data)
clustering_users()
# --- clustering_users_with_threshold: simplified method
clustering_users_with_threshold()
# ==================================================================== #

