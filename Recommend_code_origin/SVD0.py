<<<<<<< HEAD
from sklearn.model_selection import train_test_split
from sklearn.utils.extmath import randomized_svd
from scipy.sparse import csr_matrix
from scipy.sparse import load_npz
import numpy as np
import math
import random
import copy

def Sparse_matrix2rcd(sparse_matrix)->np.array:
    #将稀疏矩阵转化为普通形式，方便分离训练集与测试集，因为目前还没有找到直接对稀疏矩阵分离的方法
    indptr = sparse_matrix.indptr
    indices = sparse_matrix.indices
    data = sparse_matrix.data
    row,col,mydata = [],[],[]
    len_ind = len(indptr)

    indptr = indptr.tolist()
    indices = indices.tolist()
    data = data.tolist()

    for r in range(len_ind-1):
        col_list = indices[indptr[r]:indptr[r+1]]
        len_col_list = len(col_list)
        if len_col_list == 0:
            continue
        col = col + col_list
        row = row + [r for i in range(len_col_list)]  #从0开始
        mydata = mydata + data[indptr[r]:indptr[r+1]]
    return np.array(row),np.array(col),np.array(mydata)


def Cal_deviation(sparse_matrix_train):
    #利用稀疏矩阵求用户偏差和物品偏差，使用均值代替
    sum_row = sparse_matrix_train.sum(axis=1) #求每行的和，返回np矩阵 2000*1
    sum_col = sparse_matrix_train.sum(axis=0) #求每列的和，返回np矩阵 1*2000

    r_nonzero,c_nonzero = sparse_matrix_train.nonzero()
    len_nonzero = len(r_nonzero)
    r_max = np.max(r_nonzero)  #最大用户编号
    c_max = np.max(c_nonzero)  #最大物品编号
    # print(r_max,c_max)
    user_deviation,item_deviation = np.zeros(r_max+1),np.zeros(c_max+1)
    item_nonzero = np.zeros(len_nonzero)
    cnt = 1
    for i in range(1,len_nonzero):
        if(r_nonzero[i] != r_nonzero[i-1]):
            user_deviation[r_nonzero[i-1]] = sum_row[r_nonzero[i-1],0] / cnt
            cnt = 1
        else:
            cnt += 1
    
    for i in range(0,len_nonzero):
        item_nonzero[c_nonzero[i]] += 1
    for i in range(0,c_max+1):
        if(item_nonzero[i] != 0):
            item_deviation[i] = sum_col[0,i] / item_nonzero[i]
    
    return user_deviation,item_deviation

def Mean_centered(row_train,col_train,data_train,user_deviation,item_deviation,r_max,c_max):
    #均值中心化，每个用户减去自己评分的均值，每个物品减去自己评分的均值
    len_data = len(data_train)
    data_train2 = copy.deepcopy(data_train)
    for i in range(len_data):
        data_train2[i] -= (user_deviation[row_train[i]] + item_deviation[col_train[i]])
    return csr_matrix((data_train2,(row_train,col_train)),shape = (r_max+1,c_max+1))

def getUp(U,user_deviation):
    #在潜在因子模型嵌入用户偏差
    user_deviation = user_deviation.reshape(len(user_deviation),1)  #不会原地改变
    Up = np.append(U,user_deviation,axis = 1)
    # print(user_deviation.shape,Up.shape)
    m,k = Up.shape
    Ones = np.ones((m,1))
    # print(Up.shape,Ones.shape)
    Up = np.append(Up,Ones,axis = 1)
    # print(Up.shape)
    return Up

def getVTp(VT,item_deviation):
    #在潜在因子模型嵌入物品偏差
    item_deviation = item_deviation.reshape(1,len(item_deviation))
    k,n = VT.shape
    Ones = np.ones((1,n))
    # print(VT.shape,Ones.shape)
    VTp = np.append(VT,Ones,axis = 0)
    VTp = np.append(VTp,item_deviation,axis = 0)
    return VTp

#随机梯度下降
def Gradient_descent(rcd_train,U,VT,alpha,landa_u,landa_i):
    m,k = U.shape
    k,n = VT.shape
    Ui,VTi = np.zeros((m,k)),np.zeros((k,n))
    c = rcd_train[0].shape[0]
    print(m,k,n)
    # print(rcd_train[:][0])
    # while():
    # print('hi',c)
    shuffle_list = [i for i in range(c)]
    # print(shuffle_list)
    for l in range(100):
        print(l)
        random.shuffle(shuffle_list)
        # rcd_train = rcd_train[:,shuffle_list]
        rcd_train_shuffle = copy.deepcopy(rcd_train)
        for i in range(c):
            # print(shuffle_list[i])
            rcd_train_shuffle[:,i] = rcd_train[:,shuffle_list[i]]
        rcd_train = copy.deepcopy(rcd_train_shuffle)
        for i in range(c-1):
            e = (rcd_train[2][i] - sum(U[int(rcd_train[0,i]),:] * VT[:,int(rcd_train[1,i])]) )  #这里的乘法为向量内积
            # print('haha',i,int(rcd_train[0,i]),int(rcd_train[1,i]))
            # print('e',e)
            # print(sum(U[int(rcd_train[0,i]),:] * VT[:,int(rcd_train[1,i])]))
            # print(e)
            for j in range(k):
                # print('U[]',U[int(rcd_train[0,i]),j])
                # print('Uo',alpha * (e*VT[j,int(rcd_train[1,i])] - landa_u*U[int(rcd_train[0,i]),j]))
                Ui[int(rcd_train[0,i]),j] = U[int(rcd_train[0,i]),j] + alpha * (e*VT[j,int(rcd_train[1,i])] - landa_u*U[int(rcd_train[0,i]),j])
                VTi[j,int(rcd_train[1,i])] = VT[j,int(rcd_train[1,i])] + alpha * (e*U[int(rcd_train[0,i]),j]  - landa_i*VT[j,int(rcd_train[1,i])])
                # print(j,' ',alpha * e*VT[j,int(rcd_train[1,i])],alpha * e*U[int(rcd_train[0,i]),j])
            # e2 = (rcd_train[2][i] - sum(Ui[int(rcd_train[0,i]),:] * VTi[:,int(rcd_train[1,i])]) )
            # print('e2',e2)
            # print(sum(Ui[int(rcd_train[0,i]),:] * VTi[:,int(rcd_train[1,i])]))
            for j in range(k):
                U[int(rcd_train[0,i]),j] = Ui[int(rcd_train[0,i]),j]
                VT[j,int(rcd_train[1,i])] = VTi[j,int(rcd_train[1,i])]
        # print('U'*60)
        # print(U[:,k-2])
        # print('VT'*60)
        # print(VT[k-1,:])
        U[:,k-1] = np.ones(m)
        VT[k-2,:] = np.ones(n)
    return U,VT
        
def Get_RSE(Rate,X_test,y_test):
    #计算准确率
    r,c = X_test.shape
    RSE = 0.0
    for i in range(r):
        RSE += (y_test[i] - Rate[X_test[i,0],X_test[i,1]])**2
    return math.sqrt(RSE/r)
def getMAE(Rate,X_test,y_test):
    r,c = X_test.shape
    MAE = 0.0
    for i in range(r):
        MAE += math.fabs(y_test[i] - Rate[X_test[i,0],X_test[i,1]])
    return MAE/r
def test():
    sparse_matrix = load_npz('E:\MyProject\Recommend_code_origin\sparse_matrix_100k.npz')  #需要绝对路径
    row,col,data =Sparse_matrix2rcd(sparse_matrix)
    len_row = len(row)
    row = row.reshape(len_row,1)
    col = col.reshape(len_row,1)
    r_max = np.max(row)
    c_max = np.max(col)

    X = np.append(row,col,axis = 1)
    X_train,X_test,y_train,y_test = train_test_split(X,data,test_size = 0.3,random_state = 42)
    sparse_matrix_train = csr_matrix((y_train,(X_train[:,0],X_train[:,1])),shape = (r_max+1,c_max+1))
    user_deviation,item_deviation = Cal_deviation(sparse_matrix_train) #求用户偏差和物品偏差
    #均值中心化
    row_train,col_train,data_train = Sparse_matrix2rcd(sparse_matrix_train)
    print('nihao1')
    # print(data_train)
    sparse_matrix_train_mean = Mean_centered(row_train,col_train,data_train,user_deviation,item_deviation,r_max,c_max)
    # print(data_train)
    U0,Sigma,VT = randomized_svd(sparse_matrix_train_mean,n_components = int(math.pow(len_row,0.66))//20)
    U = U0*Sigma
    # print('U')
    # print(U)
    # print('VT')
    # print(VT)
    # print('UVT')
    # print(type(U))
    # print(type(VT))
    # print(U.shape,VT.shape)
    # print(np.dot(U,VT))
    # print('*'*60)
    # print(sparse_matrix_train_mean)
    # print(U.shape,VT.shape)
    # print(type(U))
    #矩阵拓展引入用户偏差和物品偏差
    #用户偏差拓展
    Up = getUp(U,user_deviation)
    VTp = getVTp(VT,item_deviation)
    print(Up)
    print('*'*60)
    print(VTp)
    print(Up.shape,VTp.shape)  #(944, 101) (101, 1683)
    #梯度下降法学习（随机）
    # print(type(row_train))
    rcd_train = np.array([row_train,col_train,data_train])  #rcd训练数据，未均值中心化,列表里面是数组
    print(rcd_train)
    rcd_train = np.array([row_train,col_train,data_train])  #rcd训练数据，未均值中心化,列表里面是数组
    print(rcd_train)
    # print('*'*60)
    # print(np.dot(Up,VTp) - rcd_train)
    S = np.dot(Up,VTp)
    sum0 = 0.0
    for i in range(len(rcd_train)):
        sum0 += math.fabs(rcd_train[2,i] - S[int(rcd_train[0,i]),int(rcd_train[1,i])])
    print(sum0)  #3.06
    sum1 = 0.0
    for i in range(len(y_test)):
        sum1 += math.fabs(y_test[i] - S[int(X_test[i,0]),int(X_test[i,1])])
    print(sum1)  #91124.5
    # print(rcd_train[:,0])
    # print(rcd_train.shape)
    # print(row_train)
    # print(col_train)
    # print(data_train)
    # print(type(rcd_train[0]))
    alpha = 0.0001
    landa_u,land_i = 0.25,0.25
    U,VT = Gradient_descent(rcd_train,Up,VTp,alpha,landa_u,land_i)
    Rate = np.dot(U,VT)
    sum0 = 0
    for i in range(len(rcd_train)):
        sum0 += math.fabs(rcd_train[2,i] - Rate[int(rcd_train[0,i]),int(rcd_train[1,i])])
    print(sum0)#1.69(10),1.18(20),0.38(40),0.48(100)
    sum1 = 0.0
    for i in range(len(y_test)):
        sum1 += math.fabs(y_test[i] - Rate[int(X_test[i,0]),int(X_test[i,1])])
    print(sum1)  #573188(10),51992(20),46243(40),36958(100)
    RSE = Get_RSE(Rate,X_test,y_test)
    print(RSE)#2.29(10)，2.13(20),1.93(40),1.57(100)
    MAE = getMAE(Rate,X_test,y_test)
    print(MAE)

if __name__ == '__main__':
=======
from sklearn.model_selection import train_test_split
from sklearn.utils.extmath import randomized_svd
from scipy.sparse import csr_matrix
from scipy.sparse import load_npz
import numpy as np
import math
import random
import copy

def Sparse_matrix2rcd(sparse_matrix)->np.array:
    #将稀疏矩阵转化为普通形式，方便分离训练集与测试集，因为目前还没有找到直接对稀疏矩阵分离的方法
    indptr = sparse_matrix.indptr
    indices = sparse_matrix.indices
    data = sparse_matrix.data
    row,col,mydata = [],[],[]
    len_ind = len(indptr)

    indptr = indptr.tolist()
    indices = indices.tolist()
    data = data.tolist()

    for r in range(len_ind-1):
        col_list = indices[indptr[r]:indptr[r+1]]
        len_col_list = len(col_list)
        if len_col_list == 0:
            continue
        col = col + col_list
        row = row + [r for i in range(len_col_list)]  #从0开始
        mydata = mydata + data[indptr[r]:indptr[r+1]]
    return np.array(row),np.array(col),np.array(mydata)


def Cal_deviation(sparse_matrix_train):
    #利用稀疏矩阵求用户偏差和物品偏差，使用均值代替
    sum_row = sparse_matrix_train.sum(axis=1) #求每行的和，返回np矩阵 2000*1
    sum_col = sparse_matrix_train.sum(axis=0) #求每列的和，返回np矩阵 1*2000

    r_nonzero,c_nonzero = sparse_matrix_train.nonzero()
    len_nonzero = len(r_nonzero)
    r_max = np.max(r_nonzero)  #最大用户编号
    c_max = np.max(c_nonzero)  #最大物品编号
    # print(r_max,c_max)
    user_deviation,item_deviation = np.zeros(r_max+1),np.zeros(c_max+1)
    item_nonzero = np.zeros(len_nonzero)
    cnt = 1
    for i in range(1,len_nonzero):
        if(r_nonzero[i] != r_nonzero[i-1]):
            user_deviation[r_nonzero[i-1]] = sum_row[r_nonzero[i-1],0] / cnt
            cnt = 1
        else:
            cnt += 1
    
    for i in range(0,len_nonzero):
        item_nonzero[c_nonzero[i]] += 1
    for i in range(0,c_max+1):
        if(item_nonzero[i] != 0):
            item_deviation[i] = sum_col[0,i] / item_nonzero[i]
    
    return user_deviation,item_deviation

def Mean_centered(row_train,col_train,data_train,user_deviation,item_deviation,r_max,c_max):
    #均值中心化，每个用户减去自己评分的均值，每个物品减去自己评分的均值
    len_data = len(data_train)
    data_train2 = copy.deepcopy(data_train)
    for i in range(len_data):
        data_train2[i] -= (user_deviation[row_train[i]] + item_deviation[col_train[i]])
    return csr_matrix((data_train2,(row_train,col_train)),shape = (r_max+1,c_max+1))

def getUp(U,user_deviation):
    #在潜在因子模型嵌入用户偏差
    user_deviation = user_deviation.reshape(len(user_deviation),1)  #不会原地改变
    Up = np.append(U,user_deviation,axis = 1)
    # print(user_deviation.shape,Up.shape)
    m,k = Up.shape
    Ones = np.ones((m,1))
    # print(Up.shape,Ones.shape)
    Up = np.append(Up,Ones,axis = 1)
    # print(Up.shape)
    return Up

def getVTp(VT,item_deviation):
    #在潜在因子模型嵌入物品偏差
    item_deviation = item_deviation.reshape(1,len(item_deviation))
    k,n = VT.shape
    Ones = np.ones((1,n))
    # print(VT.shape,Ones.shape)
    VTp = np.append(VT,Ones,axis = 0)
    VTp = np.append(VTp,item_deviation,axis = 0)
    return VTp

#随机梯度下降
def Gradient_descent(rcd_train,U,VT,alpha,landa_u,landa_i):
    m,k = U.shape
    k,n = VT.shape
    Ui,VTi = np.zeros((m,k)),np.zeros((k,n))
    c = rcd_train[0].shape[0]
    print(m,k,n)
    # print(rcd_train[:][0])
    # while():
    # print('hi',c)
    shuffle_list = [i for i in range(c)]
    # print(shuffle_list)
    for l in range(100):
        print(l)
        random.shuffle(shuffle_list)
        # rcd_train = rcd_train[:,shuffle_list]
        rcd_train_shuffle = copy.deepcopy(rcd_train)
        for i in range(c):
            # print(shuffle_list[i])
            rcd_train_shuffle[:,i] = rcd_train[:,shuffle_list[i]]
        rcd_train = copy.deepcopy(rcd_train_shuffle)
        for i in range(c-1):
            e = (rcd_train[2][i] - sum(U[int(rcd_train[0,i]),:] * VT[:,int(rcd_train[1,i])]) )  #这里的乘法为向量内积
            # print('haha',i,int(rcd_train[0,i]),int(rcd_train[1,i]))
            # print('e',e)
            # print(sum(U[int(rcd_train[0,i]),:] * VT[:,int(rcd_train[1,i])]))
            # print(e)
            for j in range(k):
                # print('U[]',U[int(rcd_train[0,i]),j])
                # print('Uo',alpha * (e*VT[j,int(rcd_train[1,i])] - landa_u*U[int(rcd_train[0,i]),j]))
                Ui[int(rcd_train[0,i]),j] = U[int(rcd_train[0,i]),j] + alpha * (e*VT[j,int(rcd_train[1,i])] - landa_u*U[int(rcd_train[0,i]),j])
                VTi[j,int(rcd_train[1,i])] = VT[j,int(rcd_train[1,i])] + alpha * (e*U[int(rcd_train[0,i]),j]  - landa_i*VT[j,int(rcd_train[1,i])])
                # print(j,' ',alpha * e*VT[j,int(rcd_train[1,i])],alpha * e*U[int(rcd_train[0,i]),j])
            # e2 = (rcd_train[2][i] - sum(Ui[int(rcd_train[0,i]),:] * VTi[:,int(rcd_train[1,i])]) )
            # print('e2',e2)
            # print(sum(Ui[int(rcd_train[0,i]),:] * VTi[:,int(rcd_train[1,i])]))
            for j in range(k):
                U[int(rcd_train[0,i]),j] = Ui[int(rcd_train[0,i]),j]
                VT[j,int(rcd_train[1,i])] = VTi[j,int(rcd_train[1,i])]
        # print('U'*60)
        # print(U[:,k-2])
        # print('VT'*60)
        # print(VT[k-1,:])
        U[:,k-1] = np.ones(m)
        VT[k-2,:] = np.ones(n)
    return U,VT
        
def Get_RSE(Rate,X_test,y_test):
    #计算准确率
    r,c = X_test.shape
    RSE = 0.0
    for i in range(r):
        RSE += (y_test[i] - Rate[X_test[i,0],X_test[i,1]])**2
    return math.sqrt(RSE/r)
def test():
    sparse_matrix = load_npz('E:\MyProject\Recommend_code_origin\sparse_matrix_100k.npz')  #需要绝对路径
    row,col,data =Sparse_matrix2rcd(sparse_matrix)
    len_row = len(row)
    row = row.reshape(len_row,1)
    col = col.reshape(len_row,1)
    r_max = np.max(row)
    c_max = np.max(col)

    X = np.append(row,col,axis = 1)
    X_train,X_test,y_train,y_test = train_test_split(X,data,test_size = 0.3,random_state = 42)
    sparse_matrix_train = csr_matrix((y_train,(X_train[:,0],X_train[:,1])),shape = (r_max+1,c_max+1))
    user_deviation,item_deviation = Cal_deviation(sparse_matrix_train) #求用户偏差和物品偏差
    #均值中心化
    row_train,col_train,data_train = Sparse_matrix2rcd(sparse_matrix_train)
    print('nihao1')
    # print(data_train)
    sparse_matrix_train_mean = Mean_centered(row_train,col_train,data_train,user_deviation,item_deviation,r_max,c_max)
    # print(data_train)
    U0,Sigma,VT = randomized_svd(sparse_matrix_train_mean,n_components = int(math.pow(len_row,0.66))//20)
    U = U0*Sigma
    # print('U')
    # print(U)
    # print('VT')
    # print(VT)
    # print('UVT')
    # print(type(U))
    # print(type(VT))
    # print(U.shape,VT.shape)
    # print(np.dot(U,VT))
    # print('*'*60)
    # print(sparse_matrix_train_mean)
    # print(U.shape,VT.shape)
    # print(type(U))
    #矩阵拓展引入用户偏差和物品偏差
    #用户偏差拓展
    Up = getUp(U,user_deviation)
    VTp = getVTp(VT,item_deviation)
    print(Up)
    print('*'*60)
    print(VTp)
    print(Up.shape,VTp.shape)  #(944, 101) (101, 1683)
    #梯度下降法学习（随机）
    # print(type(row_train))
    rcd_train = np.array([row_train,col_train,data_train])  #rcd训练数据，未均值中心化,列表里面是数组
    print(rcd_train)
    rcd_train = np.array([row_train,col_train,data_train])  #rcd训练数据，未均值中心化,列表里面是数组
    print(rcd_train)
    # print('*'*60)
    # print(np.dot(Up,VTp) - rcd_train)
    S = np.dot(Up,VTp)
    sum0 = 0.0
    for i in range(len(rcd_train)):
        sum0 += math.fabs(rcd_train[2,i] - S[int(rcd_train[0,i]),int(rcd_train[1,i])])
    print(sum0)  #3.06
    sum1 = 0.0
    for i in range(len(y_test)):
        sum1 += math.fabs(y_test[i] - S[int(X_test[i,0]),int(X_test[i,1])])
    print(sum1)  #91124.5
    # print(rcd_train[:,0])
    # print(rcd_train.shape)
    # print(row_train)
    # print(col_train)
    # print(data_train)
    # print(type(rcd_train[0]))
    alpha = 0.0001
    landa_u,land_i = 0.25,0.25
    U,VT = Gradient_descent(rcd_train,Up,VTp,alpha,landa_u,land_i)
    Rate = np.dot(U,VT)
    sum0 = 0
    for i in range(len(rcd_train)):
        sum0 += math.fabs(rcd_train[2,i] - Rate[int(rcd_train[0,i]),int(rcd_train[1,i])])
    print(sum0)#1.69(10),1.18(20),0.38(40),0.48(100)
    sum1 = 0.0
    for i in range(len(y_test)):
        sum1 += math.fabs(y_test[i] - Rate[int(X_test[i,0]),int(X_test[i,1])])
    print(sum1)  #573188(10),51992(20),46243(40),36958(100)
    RSE = Get_RSE(Rate,X_test,y_test)
    print(RSE)#2.29(10)，2.13(20),1.93(40),1.57(100)

if __name__ == '__main__':
>>>>>>> 1052bd7f311aaf5716fa692d2d58b7c059c64025
    test()