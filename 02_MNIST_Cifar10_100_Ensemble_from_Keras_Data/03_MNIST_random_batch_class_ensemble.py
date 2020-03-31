import tensorflow as tf
import numpy as np
import time, datetime
import random
from keras.utils import np_utils
tf.set_random_seed(777)  # reproducibility
# 최신 Windows Laptop에서만 사용할것.CPU Version이 높을때 사용.
# AVX를 지원하는 CPU는 Giuthub: How to compile tensorflow using SSE4.1, SSE4.2, and AVX. 
# Ubuntu와 MacOS는 지원하지만 Windows는 없었음. 2018-09-29
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Compuntational Graph Initialization
from tensorflow.python.framework import ops
ops.reset_default_graph()

# CIFAR-10 데이터를 다운로드 받기 위한 keras의 helper 함수인 load_data 함수를 임포트합니다.
from keras.datasets import mnist

# CIFAR-100 데이터를 다운로드 받기 위한 keras의 helper 함수인 load_data 함수를 임포트합니다.
# from tensorflow.keras.datasets.cifar100 import load_data

# hyper parameters
Alpha_Lr   = 0.001
N_EPISODES = 5
# batch size, 25, 50, 100, 200, 500, 1000, 2000, 5000
batch_size = 500

# dropout (keep_prob) rate  0.7~0.5 on training, but should be 1 for testing
keep_prob = tf.placeholder(tf.float32)

# for cifar 10
N_Classes = 10

# for cifar 100
# N_Classes = 100

# CIFAR-10 데이터를 다운로드하고 데이터를 불러옵니다.
(X_train, Y_train), (X_test, Y_test) = mnist.load_data()

# pre-process data
X_train = X_train.reshape(X_train.shape[0], 28, 28, 1)
X_test = X_test.reshape(X_test.shape[0], 28, 28, 1)
X_train = X_train.astype('float32')
X_test = X_test.astype('float32')
X_train /= 255
X_test /= 255

Y_train = np_utils.to_categorical(Y_train, 10)
Y_test = np_utils.to_categorical(Y_test, 10)

# 다음 배치를 읽어오기 위한 next_batch 유틸리티 함수를 정의합니다.
def Next_batch_random(num, data, labels):
    '''
    `num` 개수 만큼의 랜덤한 샘플들과 레이블들을 리턴합니다.
    '''
    idx = np.arange(0 , len(data))
    np.random.shuffle(idx)
    idx = idx[:num]
    data_shuffle = [data[ i] for i in idx]
    labels_shuffle = [labels[ i] for i in idx]

    return np.asarray(data_shuffle), np.asarray(labels_shuffle)

# CNN 모델을 정의합니다. 
class CL_Deep_CNN:

    def __init__(self, sess, name):
        self.sess = sess
        self.name = name
        self.FN_Build_Network()

    def FN_Build_Network(self):
        with tf.variable_scope(self.name):
            # dropout (keep_prob) rate  0.7~0.5 on training, but should be 1
            self.keep_prob = tf.placeholder(tf.float32)

            # input place holders
            self.X = tf.placeholder(tf.float32, shape=[None, 28, 28, 1])
            self.Y = tf.placeholder(tf.float32, shape=[None, N_Classes])
            net = self.X
            
            net = tf.layers.conv2d(net, 32, [3, 3], activation=tf.nn.relu, padding='SAME')
            net = tf.layers.max_pooling2d(net, [2, 2], [2, 2], padding='SAME')

            net = tf.layers.conv2d(net, 32, [3, 3], activation=tf.nn.relu, padding='SAME')
            net = tf.layers.max_pooling2d(net, [2, 2], [2, 2], padding='SAME')

            net = tf.layers.conv2d(net, 64, [3, 3], activation=tf.nn.relu, padding='SAME')
            net = tf.layers.conv2d(net, 64, [3, 3], activation=tf.nn.relu, padding='SAME')
            net = tf.layers.conv2d(net, 64, [3, 3], activation=tf.nn.relu, padding='SAME')
            
            net = tf.contrib.layers.flatten(net)
            net = tf.layers.dense(net, 512, activation=tf.nn.relu)
    
            net = tf.nn.dropout(net, keep_prob=self.keep_prob)
        
            logits = tf.layers.dense(net, N_Classes, activation=None)
            self.y_pred = tf.nn.softmax(logits)
            
        # define cost/loss & optimizer
        self.cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits = logits, labels=self.Y))
        self.optimizer = tf.train.AdamOptimizer(learning_rate = Alpha_Lr).minimize(self.cost)

        correct_prediction = tf.equal(tf.argmax(self.y_pred, 1), tf.argmax(self.Y, 1))
        self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

    def FN_Predict(self, x_test, keep_prob=1.0):
        return self.sess.run(self.y_pred, feed_dict={self.X: x_test, self.keep_prob: keep_prob})

    def FN_Get_Accuracy(self, x_test, y_test, keep_prob=1.0):
        return self.sess.run(self.accuracy, feed_dict={self.X: x_test, self.Y: y_test, self.keep_prob: keep_prob})

    def FN_Train_Net(self, x_data, y_data, keep_prob=0.7):
        return self.sess.run([self.cost, self.optimizer], feed_dict={
            self.X: x_data, self.Y: y_data, self.keep_prob: keep_prob})

# 세션을 열어 실제 학습을 진행합니다.
with tf.Session() as sess:
    
    models = []
    num_models = 8
    for m in range(num_models):
        models.append(CL_Deep_CNN(sess, "model" + str(m)))
    
    # 모든 변수들을 초기화한다. 
    sess.run(tf.global_variables_initializer())
    
    start_time = time.time()

    print('Learning started. It takes sometime.')

    # train my model
    # Total_batch = int(X_train.shape[0]/batch_size)
    Total_batch = 20

    for episode in range(N_EPISODES):
        avg_cost_list = np.zeros(len(models))
        for i in range(Total_batch):
            batch = Next_batch_random(batch_size, X_train, Y_train)

            # c, _ = m1.FN_Train_Net(batch[0], batch[1])
            # train each model
            for m_idx, m in enumerate(models):
                c, _ = m.FN_Train_Net(batch[0], batch[1])
                avg_cost_list[m_idx] += c / Total_batch
                # avg_cost += c / Total_batch
        
        print('episode:', '%05d' % (episode + 1), 'cost =',avg_cost_list)
        elapsed_time = datetime.timedelta(seconds=int(time.time()-start_time))
        print("[{}]".format(elapsed_time))

    print('Learning Finished!')

    # Test model and check accuracy
    test_size = int(X_test.shape[0])
    N_test_batch = int(X_test.shape[0]/batch_size)
    predictions = np.zeros([test_size, N_Classes])
    
    for m_idx, m in enumerate(models):
        test_accuracy = 0.0
        for i in range(N_test_batch):
            test_batch = Next_batch_random(batch_size, X_test, Y_test)
            test_accuracy = test_accuracy + m.FN_Get_Accuracy(test_batch[0], test_batch[1])
        test_accuracy = test_accuracy / N_test_batch;

        print("Ensemble Model ",m_idx + 1, "test data Accuracy: %2.4f" % test_accuracy)
        # print(m_idx, 'Accuracy:', m.FN_Get_Accuracy(test_batch[0], test_batch[1]))
        
        p = m.FN_Predict(X_test)
        predictions += p

    ensemble_is_correct = tf.equal(tf.argmax(predictions, 1), tf.argmax(Y_test, 1))
    ensemble_accuracy = tf.reduce_mean(tf.cast(ensemble_is_correct, tf.float32))
    print('Ensemble accuracy:', sess.run(ensemble_accuracy))

    elapsed_time = time.time() - start_time
    formatted = datetime.timedelta(seconds=int(elapsed_time))
    print("=== training time elapsed: {}s ===".format(formatted))
