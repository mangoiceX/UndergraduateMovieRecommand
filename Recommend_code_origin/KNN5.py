#KNN4.py的基础上添加评价指标
from sklearn import neighbors
import numpy as np
from sklearn import model_selection
import time
import datetime
from sklearn.decomposition import TruncatedSVD
from sklearn.utils.extmath import randomized_svd
from sklearn.neighbors import NearestNeighbors
import math
import copy
import pymysql
from LFM_sql import ReadMysql
import pickle
from sklearn.externals import joblib
import random
import operator
'''
函数解释：
    numpy的nonzero函数:
        如果是一维数组，则返回不是0的数的下标。如果是二维数组，则返回元组，第一列是非零元素的行号，第2列是列号
    numpy的argpartition函数：
         k_most_related = k_most_related[np.argpartition(k_most_related,min(k_most_related_r-1,k-1),axis=0)[0:,0]]
         如果找前k小的数，那么相应参数应该是k-1(而不是k),函数返回的是顺序矩阵，类似于nonzero。
         还有一个问题就是如果是numpy的mat矩阵，那么切片之后还是矩阵，所以目前只能访问单个元素，如果要访问一列元素，
         则原矩阵应该转化为numpy的array
'''


def Data_process(host, username, password, database) -> np.mat:
    db = pymysql.connect(host, username, password, database)
    cursor = db.cursor()
    cursor.execute("select userID, movieID, rating from ratings")
    results = cursor.fetchall()
    # userID, movieID, rating = [],[],[]
    data = np.mat(np.zeros((6100, 4100)))  # 矩阵行为用户id,列为Movie id
    print(len(results))
    testCaseLoc = random.sample(range(0,len(results)-1),int(0.2*(len(results)-1)))  #获得哪些位置作为测试集
    testCaseLoc.sort()
    # print(testCaseLoc)
    # print(len(testCaseLoc))
    cnt = 0
    testLoc = 0
    testCaseLocLen = len(testCaseLoc)
    testCase = []
    trainCase = []
    userMax,itemMax = 0,0
    for item in results:
        if testLoc < testCaseLocLen and cnt == testCaseLoc[testLoc]:
            cnt += 1
            testLoc += 1
            testCase.append([item[0]-1,item[1]-1,item[2]])
            continue
        data[item[0]-1, item[1]-1] = item[2]
        cnt += 1
        userMax = max(userMax, item[0]-1)
        itemMax = max(itemMax, item[1]-1)
        trainCase.append([item[0]-1,item[1]-1,item[2]])

    return data,trainCase,testCase,userMax,itemMax


def Mean_centered(origin_data: np.mat) -> np.mat:  #
    '''
        传入参数：
            origin_data: 原始未处理的评分矩阵 np.mat
        返回值：
            均值中心化后的数据 numpy.mat
        功能：将矩阵先行均值中心化,即每行非零元素减去非零元素的均值
    '''
    # origin_data = origin_data.T
    r, c = origin_data.shape  # 数据矩阵的行数和列数
    # 使用深拷贝，默认的等号是浅拷贝，相当于C++的引用，这是一个陷阱
    mean_centered_data = copy.deepcopy(origin_data)
    for i in range(0, r):
        mean_centered_data[i, np.nonzero(mean_centered_data[i, :])[
            1]] -= np.mean(mean_centered_data[i, np.nonzero(mean_centered_data[i, :])[1]])
    # for i in range(0,c):
    #     index = np.nonzero(mean_centered_data[:,i])
    #     # r1 = len(index[0])
    #     # print(mean_centered_data[index[0],i].shape)
    #     # print(np.mean(mean_centered_data[index[0],i]))
    #     mean_val = np.mean(mean_centered_data[index[0],i])
    #     for j in index[0]:
    #         mean_centered_data[j,i] -= mean_val
    return mean_centered_data


class KNN:
    def __init__(self,userMax = 0,itemMax = 0):
        # self.rating_denominator = None
        self.denominatorA = None
        self.denominatorB = None
        self.rating_nominator = None
        self.similarity_item_matrix = None
        self.userMax = userMax
        self.itemMax = itemMax

        # return mean_centered_data.T#和上面origin_data的转置结合起来就是列均值中心化
    def Cosine_similarity(self, inA: np.mat, inB: np.mat, item1: int, item2: int) -> float:  # 调整余弦
        '''
            传入参数：
                inA np.mat 物品的评分向量（SVD降维之后）
                overlap np.array 两个物品被同一个用户评分的用户行号
            返回值：
                相似度 float
            复杂度：O(d) d为降维后的用户维度
        '''
        # punishment_factor = [
        #     1/math.log(math.e, 2+math.fabs(a - b)) for a, b in zip(inA, inB)]
        # inA2 = [(a*b)[0, 0] for a, b in zip(inA, punishment_factor)]
        # inA2 = np.array(inA2)
        # inA2 = inA2.reshape(1, inA2.shape[0])
        # inA2 = np.mat(inA2)
        inA2 = inA
        numerator = float(inA2 * inB)
        # 存储分子
        self.rating_nominator[item1,
                              item2] = self.rating_nominator[item2, item1] = numerator
        self.denominatorA[item1, item2] = self.denominatorA[item2,
                                                            item1] = np.linalg.norm(inA)
        self.denominatorB[item1, item2] = self.denominatorB[item2,
                                                            item1] = np.linalg.norm(inB)
        denominator = self.denominatorA[item1, item2] * \
            self.denominatorB[item1, item2]  # 乘法改成加法
        # self.rating_denominator[item1,item2] = self.rating_denominator[item2,item1] = denominator ** 2 #存储分母两个元素
        return numerator/(denominator+0.0000001)

    def Pearson_similarity(self, inA: np.mat, inB: np.mat) -> float:
        '''
        传入参数：
                inA np.mat 物品的评分向量（SVD降维之后）
                overlap np.array 两个物品被同一个用户评分的用户行号
            返回值：
                相似度 float
            复杂度：O(d) d为降维后的用户维度
        '''
        return np.corrcoef(inA, inB, rowvar=0)[0][1]

    def Choose_dimension(self, Sigma: np.array, info_remain_percent: float) -> int:
        '''
            传入参数：
                Sigma:奇异值向量 np.array
                info_remain_percent:降维后的矩阵应该保留原矩阵的信息占比
            返回值；
                选取前ans个奇异值即可保留原矩阵信息的info_remain_percent,即前i个奇异值和占所有奇异值总和的比率>=info_remain_percent  int
            复杂度:O(n),n表示列的个数
        '''
        totle_sum = sum(Sigma**2)
        sum_now = 0.0
        ans = 0
        Len = len(Sigma)  # 求Sigma向量的长度
        for i in range(0, Len):
            sum_now += Sigma[i]**2
            if sum_now/totle_sum >= info_remain_percent:
                ans = i
                break
        return ans + 1

    def Calculate_items(self, origin_data: np.mat, mean_centered_data_transf: np.mat, Similarity_calculate_means) -> np.mat:
        '''
            传入参数：mean_centered_data_transf 降维后的矩阵 np.mat
                    similarity_calculate_means 相似度计算方法
            返回值：similarity_item_matrix 物品之间的相似度矩阵 np.mat
            复杂度：O(d*c1^2),d表示用户行降维后的个数，c1表示用户所评分的最大电影数，相比较，朴素算法O(c^2*d),
            第一种比第二种优，因为一个物品被评分的用户数一般>>一个用户评分的物品数
        '''
        mean_centered_data_transf = mean_centered_data_transf.T  # 将降维后的矩阵转置，使之符合原始矩阵
        r, c = mean_centered_data_transf.shape  # 分别是降维后的列数（用户维度）和 物品数

        similarity_item_matrix = np.mat(np.zeros((c, c)))
        # print("c: %d"%c)
        for i in range(0, c):
            print(i)
            for j in range(i+1, c):
                # print(i,j)
                similarity_item_matrix[i, j] = similarity_item_matrix[j, i] = Similarity_calculate_means(
                    mean_centered_data_transf[:, i], mean_centered_data_transf[:, j], i, j)
        return similarity_item_matrix

    def Calculate_items_similarty(self, origin_data: np.mat, mean_centered_data: np.mat) -> np.mat:
        '''
            传入参数：
                mean_centered_data:均值中心化后的矩阵 np.mat
            返回值；
                item之间的相似度矩阵
        '''
        self.rating_denominator = np.zeros(
            (origin_data.shape[1], origin_data.shape[1]))  # 相似度计算分母矩阵
        self.denominatorA = np.mat(
            np.zeros((origin_data.shape[1], origin_data.shape[1])))
        self.denominatorB = np.mat(
            np.zeros((origin_data.shape[1], origin_data.shape[1])))
        self.rating_nominator = np.zeros(
            (origin_data.shape[1], origin_data.shape[1]))  # 相似度计算分子矩阵
        print("svd")
        # U,Sigma,VT = np.linalg.svd(mean_centered_data)  #numpy中SVD的实现
        # dimension = self.Choose_dimension(Sigma,0.90) #计算应该降维的维度
        r, c = mean_centered_data.shape
        dimension = c//100
        U, Sigma, VT = randomized_svd(
            mean_centered_data, n_components=dimension)
        # print("用户维度降维：",dimension)
        '''
            #sklearn的截断SVD实现
            # svd = TruncatedSVD(n_components = dimension)
            # mean_centered_data_transf = svd.fit_transform(mean_centered_data) #降维后的评分矩阵
            # Sigma = svd.singular_values_
            #sklearn的随机SVD实现(近似解，相对于截断SVD速度更快)
            #截断SVD使用精确解算器ARPACK，随机SVD使用近似技术。
            r,c = mean_centered_data.shape
            dimension = r/10
            U,Sigma,VT = randomized_svd(mean_centered_data,n_components = dimension)
        '''
        print("haha")
        Sigma_dimension = np.mat(
            np.eye(dimension)*Sigma[:dimension])  # 将奇异值向量转换为奇异值矩阵
        # print(Sigma_dimension)
        # print('nihao:',Sigma)
        # print(U[:,:dimension])
        mean_centered_data_transf = mean_centered_data.T * \
            U[:, :dimension]*Sigma_dimension.I  # 降维后的评分矩阵
        # print(mean_centered_data_transf)
        # print("奇异值分解，且降维后的矩阵：\n",mean_centered_data_transf.T)
        print("nihao1")
        self.similarity_item_matrix = self.Calculate_items(
            origin_data, mean_centered_data_transf, self.Cosine_similarity)  # Pearson_similarity
        # return self.similarity_item_matrix

    def ItemRecommend2(self, origin_data: np.mat, mean_centered_data: np.mat, metric: str, user: int, k: int, predict_num: int, recommend_reasons_num: int) -> np.array:
        U, Sigma, VT = np.linalg.svd(mean_centered_data)  # numpy中SVD的实现
        dimension = self.Choose_dimension(Sigma, 0.90)  # 计算应该降维的维度
        Sigma_dimension = np.mat(
            np.eye(dimension)*Sigma[:dimension])  # 将奇异值向量转换为奇异值矩阵
        mean_centered_data_transf = mean_centered_data.T * \
            U[:, :dimension]*Sigma_dimension.I  # 降维后的评分矩阵
        # print(mean_centered_data_transf.shape)
        mean_centered_data_transf = mean_centered_data_transf.T
        # print(mean_centered_data_transf.shape)
        # mean_centered_data_transf = mean_centered_data_transf.T
        # mean_centered_data_transf = np.array(mean_centered_data_transf)
        user -= 1
        rated_item = np.nonzero(origin_data[user, :] > 0)[1]  # 获得目标用户已评分的物品的标号

        unrated_item = np.nonzero(origin_data[user, :] < 0.5)[
            1]  # 获得目标用户未评分的物品的标号

        len_unrated_item = len(unrated_item)
        predict_rating = np.array(
            np.zeros((len_unrated_item+5, 2+recommend_reasons_num)))
        for i in range(0, len_unrated_item):
            model_knn = NearestNeighbors(algorithm='ball_tree')

            model_knn.fit(mean_centered_data_transf[:, rated_item].T)

            distances, indices = model_knn.kneighbors(mean_centered_data_transf[:, unrated_item[i]].T  # 必须是行向量
                                                      , n_neighbors=k)
            similarities = distances.flatten() - 1
            sum_similarities = sum(similarities)

            k_most_related = np.array(np.zeros((k, 2)))
            for j in range(0, k):
                predict_rating[i][0] += similarities[j] * \
                    origin_data[user, rated_item[indices.flatten()[j]]]
                k_most_related[j][0] = similarities[j]
                # 不是直接使用indices[0][j]
                k_most_related[j][1] = rated_item[indices[0][j]]
            if math.fabs(sum_similarities - 0) < 1e-2:
                predict_rating[i][0] = -1
            else:
                predict_rating[i][0] /= sum_similarities
                predict_rating[i][1] = unrated_item[i]

            recommend_reasons_items = k_most_related[np.argpartition(k_most_related, min(
                recommend_reasons_num-1, k-1), axis=0)[0:min(recommend_reasons_num, k), 0]][:, 1]
            predict_rating[i][2:min(
                2+recommend_reasons_num, 2+k)] = recommend_reasons_items
        predict_rating = predict_rating[np.argpartition(predict_rating[0:len_unrated_item], min(
            len_unrated_item-1, predict_num-1), axis=0)[0:min(len_unrated_item, predict_num), 0]]
        predict_rating = predict_rating[predict_rating[:, 0].argsort()]
        predict_rating = predict_rating[::-1, :]
        r2, c2 = predict_rating.shape

        score = predict_rating[:, 0]
        pos = predict_rating[:, 1]
        recommend_reasons_items_final = predict_rating[:, 2:min(
            2+recommend_reasons_num, 2+k)]  # 最优物品编号
        score, pos = np.array(score), np.array(pos)
        top_k_item = pos[0:predict_num]  # 评分最高的物品在unrated_item中的位置
        top_k_score = score[0:predict_num]
        return top_k_item, top_k_score, recommend_reasons_items_final

    def ItemRecommend(self, origin_data: np.mat, user: int, k: int, predict_num: int) -> np.array:
        '''
            传入参数：similarity_item_matrix np.mat 物品相似度矩阵
                    data np.mat  原始评分矩阵
                    user int 要推荐的用户的id
                    k int 预测未评分物品分数时，参考的最近邻的个数
                    predict_num int 推荐电影的个数 
            返回值：  unrated[top_k]   推荐物品的id
            复杂度：  O(n1*n2) n1表示已评分的个数，n2表示未评分的个数
        '''
        user -= 1  # user从0开始
        r, c = origin_data.shape

        rated_item = np.nonzero(origin_data[user, :] > 0)[1]  # 获得目标用户已评分的物品的标号
        # print('ra',rated_item)
        unrated_item = np.nonzero(origin_data[user, :] < 0.5)[
            1]  # 获得目标用户未评分的物品的标号
        # print('un',unrated_item)
        len1 = len(rated_item)
        len2 = len(unrated_item)
        # print(len1, len2)
        # print(similarity_item_matrix)

        recommend_reasons_num = 2
        #因为实际情况必然是对当前预测正效应的物品较多(>=3),所以不用特意去筛选负效应的物品，因为负效应的物品（或者是正效应很小的物品）不应该出现在推荐理由上
        # 第一列存储相似度，第二列存储物品的标号,后面(5-2)存储5-2个推荐理由
        predict_rating = np.array(np.ones((len2+5, 2+recommend_reasons_num)))
        #predict_ratiing创建初始化为0，可能初始值0与推荐物品编号冲突，但并不会，因为后面坐了切片，后面无效的0都被舍去了

        for i in range(0, len2):  # 未评分的物品
            # 第i个未评分的物品与所有已评分物品的相似度，然后筛选出k近邻
            k_most_related = np.array(np.zeros((len1+5, 2)))
            for j in range(0, len1):  # 评分的物品
                # 当前第i个未评分的物品与第j个评分物品的相似度
                k_most_related[j, 0] = - \
                    self.similarity_item_matrix[rated_item[j], unrated_item[i]]
                # 相似度，添加符号转化为k小值，存储在原数据矩阵的下标
                k_most_related[j, 1] = rated_item[j]
            '''
                numpy argpartition 返回每一列的前K个值的位置(axis=0时)，是一个二维矩阵
            '''

            k_most_related = k_most_related[0:len1]  # 截取前面有效的信息，已评分物品的数量
            # print(k_most_related)
            # print(k_most_related.shape)
            k_most_related_r, k_most_related_c = k_most_related.shape
            # print(k_most_related)
            k_most_related = k_most_related[np.argpartition(k_most_related, min(
                k_most_related_r-1, k-1), axis=0)[0:, 0]]  # 小的放前面，min(k_most_related_r-1,k-1),因为已评分的物品小于k个
            # print('nihao1',k_most_related[:,0])
            # print(sum(k_most_related[:,0]))
            # print(origin_data[user,(k_most_related[:,1]).astype(np.int32)])
            # predict_score = np.inner(k_most_related[:,0] , np.array((origin_data[user,(k_most_related[:,1]).astype(np.int32)])))/sum(np.fabs(k_most_related[:,0]))
            numerator = 0.0
            denominator = 0.0
            # print(k_most_related[np.argpartition(k_most_related,min(recommend_reasons_num-1,k_most_related_r-1),axis = 0)[0:,0]])
            recommend_reasons_items = k_most_related[np.argpartition(k_most_related, min(
                recommend_reasons_num-1, k_most_related_r-1), axis=0)[0:min(recommend_reasons_num, k_most_related_r), 0]][:, 1]
            for v in k_most_related:
                if v[0] < 0:  # 只计算正效应（相似度为正的物品），前面为了取前k大，每个相似度添加了负号，转化为前k小
                    numerator += v[0]*origin_data[user, int(v[1])]
                    denominator += np.fabs(v[0])

            if np.fabs(denominator - 0.0) <= 1e-2:
                predict_score = 0
            else:
                predict_score = numerator/denominator
                '''
                    如果不除以分母，预测评分偏差会比较大（偏大），如果除以分母,考虑一种极端情况，如果一个用户的所有评分都是一样的
                    那么预测评分都会是这个相同的分数
                '''
            predict_rating[i, 0] = predict_score  # 第i个未评分物品的预测分数
            # print(predict_score)
            predict_rating[i, 1] = unrated_item[i]  # 相应的物品编号
            # print(recommend_reasons_items.shape)
            # print(recommend_reasons_items)
            # 存储推荐理由物品的编号，因为你看过...
            predict_rating[i, 2:min(
                2+recommend_reasons_num, 2+k_most_related_r)] = recommend_reasons_items

        # item  = np.argpartition(predict_rating[:],predict_num,axis = 0)[0:k,:]
        # print(predict_rating)

        #[0:min(len2,predict_num),0],不是[0:min(len2,predict_num)-1,0]，因为区间是左闭右开
        predict_rating = predict_rating[np.argpartition(predict_rating[0:len2], min(
            len2-1, predict_num-1), axis=0)[0:min(len2, predict_num), 0]]
        #上面的predict_rating[0:len2]切片舍弃了无效信息

        # print('fddfdsadf:\n',predict_rating)
        # predict_rating = np.sort(predict_rating[0,:],axis = 0)
        predict_rating = predict_rating[predict_rating[:, 0].argsort()]
        # print(predict_rating)
        # pos = predict_rating[:-1,1].astype(np.int32)
        # print(pos)
        # print(origin_data[:,pos[0]])
        # print(pos)
        r2, c2 = predict_rating.shape
        # print(predict_rating)
        # score,pos = [],[]
        # for i in range(r2-1,-1,-1):
        #     score.append(predict_rating[i][0])
        #     pos.append(predict_rating[i][1])
        # print(predict_rating[i][0],predict_rating[i][1])
        # print(predict_rating)
        score = -predict_rating[:, 0]
        pos = predict_rating[:, 1]
        recommend_reasons_items_final = predict_rating[:, 2:min(
            2+recommend_reasons_num, 2+k_most_related_r)]  # 最优物品编号
        # print(predict_rating.shape)
        # print(pos,score)
        # score = predict_rating[k-predict_num:-1,0]
        # print('nimei:',score)
        # print(pos)
        score, pos = np.array(score), np.array(pos)
        top_k_item = pos[0:predict_num]  # 评分最高的物品在unrated_item中的位置
        top_k_score = score[0:predict_num]
        return top_k_item, top_k_score, recommend_reasons_items_final

    def Increment_update(self, user, item, rating, origin_data):  # origin_data是引用传递，因为他是可变变量
        #增量更新
        user -= 1
        item -= 1
        origin_data[user, item] = rating
        user_item = np.nonzero(origin_data[user, :])[1]
        user_av = np.mean(origin_data[user, user_item])
        for item1 in user_item:
            # print(item1)
            if(item1 == item):
                continue
            else:
                r0 = origin_data[user, item]
                r1 = origin_data[user, item1]
                self.rating_nominator[item1, item] = self.rating_nominator[item, item1] = (
                    self.rating_nominator[item1, item] + (r0 - user_av) * (r1 - user_av) )
                # print(type(denominatorA))
                self.denominatorA[item, item1] = self.denominatorA[item1, item] = (
                    self.denominatorA[item1, item] + (r0 - user_av) ** 2)
                self.denominatorB[item, item1] = self.denominatorB[item1, item] = (
                    self.denominatorB[item1, item] + (r1 - user_av) ** 2)
                # self.rating_denominator[item,item1] = self.rating_denominator[item1,item] = (self.denominatorA[item,item1] * self.denominatorB[item1,item])
                tmp = (self.denominatorA[item, item1]
                       * self.denominatorB[item1, item])
                self.similarity_item_matrix[item,
                                            item1] = self.similarity_item_matrix[item1, item] = tmp / math.sqrt(self.rating_nominator)
    
    def predictRating(self,user,movie,origin_data,topK):
        rated_item = np.nonzero(origin_data[user, :] > 0)[1]
        # print(rated_item)
        # print(len(rated_item))
        # print(self.similarity_item_matrix.shape)
        similarities = []
        for item in rated_item:
            similarities.append(self.similarity_item_matrix[movie,item])
        # similarities = self.similarity_item_matrix[movie,rated_item]
        # print(len(similarities)-1)
        similary_item = np.argpartition(similarities,min(topK-1,len(similarities)-1),axis=0)[0:]
        # print(similary_item)
        similarities_sum = 0.0
        rating = 0.0
        cnt = 0
        for i in range(min(topK,len(similarities))):
            # if cnt < 3:
            #     cnt += 1
            #     print("相似度")
            #     print(similarities[similary_item[i]],
            # origin_data[user, rated_item[similary_item[i]]])
            # self.similarity_item_matrix[movie,similary_item[i]]
            rating +=  similarities[similary_item[i]] * origin_data[user,rated_item[similary_item[i]]]
            similarities_sum += math.fabs(similarities[similary_item[i]])
        final = math.fabs(rating / similarities_sum)
        final = max(min(5.0,final),0.0)
        return final

    def getRMSEandMAE(self,origin_data,testCase,topK):
        RMSE = 0.0
        MAE = 0.0
        cnt = 1 
        for item in testCase:
            # print(item)
            user, movie, rating = item[0], item[1], item[2]
            predict_rating = self.predictRating(user, movie, origin_data,5)
            if cnt < 100:
                cnt += 1
                print("预测评分")
                print(predict_rating, rating)
            RMSE += (predict_rating - rating) ** 2
            MAE += math.fabs(predict_rating - rating)
        return math.sqrt(RMSE/len(testCase)), MAE/len(testCase)

    def getCoverage(self, origin_data, testCase, topK):
        recommend_list = []
        predict_num = 5
        for item in testCase:
            user,movie,rating = item[0],item[1],item[2]
            top_k_item, top_k_score, recommend_reasons_items_final = self.ItemRecommend(origin_data,user,topK,predict_num)
            recommend_list = recommend_list + top_k_item
        coverage = len(set(recommend_list)) / self.itemMax  #推荐物品的覆盖率
        times = {}
        for i in set(recommend_list):
            times[i] = recommend_list.count(i)
        j = 1
        n = len(times)
        G = 0
        for item,weight in sorted(times.items(),key=operator.itemgetter(1)):
            G += (2*j-n-1)*weight
        return coverage, G/float(n-1)

    def getCoverage2(self,trainCase):
        itemList = np.array(trainCase)[:,1]
        itemList = list(itemList)
        trainCoverage = len(set(itemList))/self.itemMax
        times = {}
        for i in set(itemList):
            times[i] = itemList.count(i)
        j = 1
        n = len(times)
        G = 0
        for item, weight in sorted(times.items(), key=operator.itemgetter(1)):
            G += (2*j-n-1)*weight
        return trainCoverage, G/float(n-1)


def test(user, k=5, predict_num=5):
    host = "localhost"
    username = "root"
    password = "112803"
    database = "mrtest"

    start = time.clock()

    # # file_path = 'E:\Bigdata\ml-100k\\u.data'
    origin_data,trainCase,testCase,userMax,itemMax = Data_process(host, username, password, database)
    # # print(origin_data)

    # mean_centered_data = Mean_centered(origin_data)
    # # print(mean_centered_data)  #打印均值中心化的评分矩阵
    knn = KNN(userMax,itemMax)
    print("begin")
    try:
        # with open('knn.pkl','rb') as f:
            # knn = pickle.load(f.read())
        knn = joblib.load('./knn3.m')
        # print(knn.similarity_item_matrix[0:20,0:10])
    except IOError:
        print("File not exist!")
    if knn.similarity_item_matrix is None:
        print("None")
        knn.Calculate_items_similarty(origin_data, mean_centered_data)
        joblib.dump(knn, './knn1.m')
    # print(testCase)
    print("RMSE and MAE caculate begins!")
    RMSE, MAE = knn.getRMSEandMAE(origin_data, testCase, 5)
    print("RMSE: ",RMSE)
    print("MAE: ",MAE)
    #--------------------------------------------------------------------------------------
    # output_file = open('knmdn.pkl','wb')
    # output_file.write(pickle.dumps(knn.similarity_item_matrix))
    # output_file.close()

    # print("nihao")
    # user = 5
    # k = 10
    # top_k_item, top_k_score, recommend_reasons_items = knn.ItemRecommend(
    #     origin_data, user, k, predict_num)
    # # # top_k_item,top_k_score,recommend_reasons_items = ItemRecommend2(origin_data,mean_centered_data,'minkowski',3,2,2,2)

    # for item, score, reason_items in zip(top_k_item, top_k_score, recommend_reasons_items):
    #     print()
    #     print("推荐的电影：%d\n预测用户 %d 对电影 %d 的评分为：%f" % (item+1, user, item, score))
    #     print("因为用户%d之前看过" % user, end=' ')
    #     for it in reason_items:
    #         print("电影%d" % it, end=' ')
    #     print()

    # knn.Increment_update(5, 1200, 5, origin_data)
    # print('*'*50)
    # top_k_item, top_k_score, recommend_reasons_items = knn.ItemRecommend(
    #     origin_data, user, k, predict_num)
    # # # top_k_item,top_k_score,recommend_reasons_items = ItemRecommend2(origin_data,mean_centered_data,'minkowski',3,2,2,2)

    # for item, score, reason_items in zip(top_k_item, top_k_score, recommend_reasons_items):
    #     print()
    #     print("推荐的电影：%d\n预测用户 %d 对电影 %d 的评分为：%f" % (item+1, user, item, score))
    #     print("因为用户%d之前看过" % user, end=' ')
    #     for it in reason_items:
    #         print("电影%d" % it, end=' ')
    #     print()
    # print(knn.predictRating(1-1,1197-1,origin_data,5))

    end = time.clock()

    print(end - start)


if __name__ == '__main__':
    test(192, 5, 5)

'''
    工作日志，10.31下午添加了给出推荐理由的功能，推荐你i物品，因为你看过j物品
    1.12 添加了惩罚因子（调整余弦）
'''
