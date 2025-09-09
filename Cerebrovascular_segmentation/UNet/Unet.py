#For accessing paths for directories and files
import os
#Arrays manipulations
import numpy as np
#Plotting library:
from matplotlib import pyplot, cm
#Reading excel files and accessing specific cells:
from openpyxl import load_workbook
#Tensorflow, Google's Deep Learning library, back end for Keras
import tensorflow as tf
#importing reading writing library 'Pickle'
import pickle

import keras

#CNN library, high level
from keras.models import model_from_json, load_model
from keras.models import Sequential, Model
from keras.layers.core import Dense, Flatten
from keras.layers import Convolution2D, MaxPooling2D, Input, Dropout, Concatenate
from keras.regularizers import l1, l2, l1_l2
from keras.optimizers import Adam, RMSprop
from keras.layers.normalization import BatchNormalization
from keras import backend as K
from keras.losses import binary_crossentropy
#Generator class for batch training of data, due to memory leak issues when complete data set used, for 3D images
#from Generate_data_segmentation_indentcorrected import DataGenerator
from Generate_data_segmentation import DataGenerator 
from keras.layers import *
from keras.engine import Layer
from keras.models import *

######-------------------------------------------------STARTING THE CODE FROM HERE------------------------------------------------------------#####
#path for Directories that contain the patches of the patient images
path = './Patches/'

#Results saving directory:
results_dir = './model/'
temp_epoch_dir = './temp_epoch_dir/'


#number of cases to be included:
number_of_cases = 40

#Size of image:
IMAGE_SHAPE = (32,32,32,1) 
OUTPUT_SHAPE = (32,32,32,1)
PATCH_PER_CASE = 1200
PATCH_TYPE1_PER_BATCH = 15
PATCH_TYPE2_PER_BATCH = 15
PATCH_TYPE3_PER_BATCH = 0
FRAC1_PATCH_TYPE1_PER_CASE = 0.5
FRAC2_PATCH_TYPE2_PER_CASE = 0.5

#Batch Size
BATCH_SIZE = 30

#Number of Epochs
SUB_EPOCHS = 200
HOW_MANY_SUB_EPOCHS = 1

#Number of outputs to be trained
#OUTPUT_SIZE = 6

#Fraction to divide the data set
VALD_FRAC = 1/5
VALD_FRAC_W = '0_2000'
IMAGE_ORDERING = 'channels_last'

#Learning rate for the model
LEARNING_RATE = 0.0001
LEARNING_RATE_W = '0_0001'

#ID for model while saving the model
MODEL_ID = 'number_of_cases_' + str(number_of_cases) + '_EPOCHS_' + str(SUB_EPOCHS*HOW_MANY_SUB_EPOCHS) + '_VALD_FRAC_' + VALD_FRAC_W + '_LR_' + LEARNING_RATE_W + '_IMSIZEHIGH_' + str(IMAGE_SHAPE[1]) + '_BATCH_SIZE_' +str(BATCH_SIZE) + '_true_labels_' + 'mean_squared_error' + '_3_convs' + '_high_rl_drop' + '_more_complex' + '_and_bigger_filters'

print('\n Input Parameters setup as follows:')
print('\n Number of cases in total: {}'.format(number_of_cases))
print('\n Shape of the input image (Shrunk down): {}'.format(IMAGE_SHAPE))
print('\n Batch size used for generators: {}'.format(BATCH_SIZE))
print('\n Total number of Epochs for training: {}'.format(SUB_EPOCHS*HOW_MANY_SUB_EPOCHS))
print('\n Fraction for Validation Cohort: {}'.format(VALD_FRAC))
print('\n Pre-defined constant learning rate: {}'.format(LEARNING_RATE))

def custom_loss(y_true,y_pred):
    return K.mean(0.01*(1-y_true)*K.binary_crossentropy(y_true,y_pred)+0.99*y_true*K.binary_crossentropy(y_true,y_pred),axis=-1)

def unbalanced_loss_hashemi(y_true,y_pred):
    beta = 1.5
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    return (1 + beta ** 2) * K.sum(y_true_f * y_pred_f) / ((1 + beta ** 2) * K.sum(y_true_f * y_pred_f) + (beta ** 2) * K.sum((1-y_pred_f)*y_true_f) + K.sum(y_pred_f * (1 - y_true_f)))

def dice_coef(y_true,y_pred):
    smooth = 1
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_coef_loss(y_true,y_pred):
    return 1-dice_coef(y_true,y_pred)

def bce_dice_loss(y_true, y_pred):
    return binary_crossentropy(y_true, y_pred) + dice_coef_loss(y_true, y_pred)

def down(filters, input_):
    down_ = Conv3D(filters, (3, 3, 3), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(input_)
    down_ = BatchNormalization(epsilon=1e-4)(down_)
    down_ = Activation('relu')(down_)
    down_ = Dropout(0.1)(down_)
    down_ = Conv3D(filters, (3, 3, 3), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(down_)
    down_ = BatchNormalization(epsilon=1e-4)(down_)
    down_res = Activation('relu')(down_)
    down_pool = MaxPooling3D((2, 2, 2), strides=(2, 2, 2), data_format=IMAGE_ORDERING)(down_)
    return down_pool, down_res

def up(filters, input_, down_high):
    up_ = UpSampling3D((2, 2, 2), data_format=IMAGE_ORDERING)(input_)
    up_ = concatenate([down_high, up_], axis=4)
    up_ = Conv3D(filters, (3, 3, 3), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(up_)
    up_ = BatchNormalization(epsilon=1e-4)(up_)
    up_ = Activation('relu')(up_)
    up_ = Dropout(0.1)(up_)
    up_ = Conv3D(filters, (3, 3, 3), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(up_)
    up_ = BatchNormalization(epsilon=1e-4)(up_)
    up_ = Activation('relu')(up_)
    return up_

def segmentation_unet(input_shape = IMAGE_SHAPE, output_size = OUTPUT_SHAPE, LR = 0.0001, num_classes = 1):
    inputs = Input(shape=input_shape)

    down0b, down0b_res = down(32, inputs)
    down0a, down0a_res = down(64, down0b)
    down0, down0_res = down(128, down0a)    
    
    center = Conv3D(256, (3, 3, 3), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(down0)
    center = BatchNormalization(epsilon=1e-4)(center)
    center = Activation('relu')(center)
    center = Dropout(0.1)(center)
    center = Conv3D(256, (3, 3, 3), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(center)
    center = BatchNormalization(epsilon=1e-4)(center)
    center = Activation('relu')(center)

    center = Conv3D(256, (1, 1, 1), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(center)
    center = BatchNormalization(epsilon=1e-4)(center)
    center = Activation('relu')(center)

    center = Conv3D(256, (1, 1, 1), kernel_regularizer=l2(0.0001), padding='same', data_format=IMAGE_ORDERING)(center)
    center = BatchNormalization(epsilon=1e-4)(center)
    center = Activation('relu')(center)

    up0 = up(128, center, down0_res)
    up0a = up(64, up0, down0a_res)
    up0b = up(32, up0a, down0b_res)

    classify = Conv3D(num_classes, (1, 1, 1), activation='sigmoid', data_format=IMAGE_ORDERING)(up0b)

    inputs_overall = [inputs]
    outputs_overall = [classify]

    model = Model(inputs=inputs_overall, outputs=outputs_overall)

    adam = Adam(lr = LEARNING_RATE)
    model.compile(loss=bce_dice_loss, optimizer=adam, metrics=[dice_coef, 'mse'])

    print(model.summary())

    return model 




all_cases = np.arange(number_of_cases)
#Setting up the training and validation partitions
vald_start_index = int( number_of_cases * (1-VALD_FRAC))
partition = {'train':all_cases[:vald_start_index],'validation':all_cases[vald_start_index:]}
print(partition['train'])
print(partition['validation'])

print('\n -----------------------Training, Validation partitions setup with Training:Validation as ' + str((1-VALD_FRAC)*100) + ':' + str((VALD_FRAC)*100) + '!!!------------------------------')

#Generators for training and validation partitions
training_generator = DataGenerator(input_shape=IMAGE_SHAPE,
                                    output_shape=OUTPUT_SHAPE,
                                    patch_per_case = PATCH_PER_CASE, 
                                    batch_size=BATCH_SIZE,
                                    patch_type1_per_batch = PATCH_TYPE1_PER_BATCH,
                                    patch_type2_per_batch = PATCH_TYPE2_PER_BATCH,
                                    patch_type3_per_batch = PATCH_TYPE3_PER_BATCH, 
                                    frac1_patch_type1_per_case = FRAC1_PATCH_TYPE1_PER_CASE,
                                    frac2_patch_type2_per_case = FRAC2_PATCH_TYPE2_PER_CASE,
                                    shuffle=True).generate(partition['train'])
validation_generator = DataGenerator(input_shape=IMAGE_SHAPE, 
                                    output_shape=OUTPUT_SHAPE, 
                                    patch_per_case = PATCH_PER_CASE, 
                                    batch_size=BATCH_SIZE,
                                    patch_type1_per_batch = PATCH_TYPE1_PER_BATCH,
                                    patch_type2_per_batch = PATCH_TYPE2_PER_BATCH,
                                    patch_type3_per_batch = PATCH_TYPE3_PER_BATCH, 
                                    frac1_patch_type1_per_case = FRAC1_PATCH_TYPE1_PER_CASE,
                                    frac2_patch_type2_per_case = FRAC2_PATCH_TYPE2_PER_CASE, 
                                    shuffle=True).generate(partition['validation'])

print('\n -----------------------Generators created for Training and Validation cohorts!!!------------------------------')

print('\n -----------------------Reading the input images and Starting to FIT the model!!!------------------------------')

model = segmentation_unet(LR = LEARNING_RATE)
print('Main Epoch: ' + str(1) + '/'+str(HOW_MANY_SUB_EPOCHS))
history = model.fit_generator(training_generator,steps_per_epoch = (len(partition['train'])*PATCH_PER_CASE)//(BATCH_SIZE),validation_data = validation_generator,validation_steps = (len(partition['validation'])*PATCH_PER_CASE)//(BATCH_SIZE),epochs = SUB_EPOCHS,verbose = 1)
# steps_per_epoch = (len(partition['train'])*PATCH_PER_CASE)//(BATCH_SIZE)
# validation_steps = (len(partition['validation'])*PATCH_PER_CASE)//(BATCH_SIZE)
model_json = model.to_json()
with open( temp_epoch_dir + 'keras_Model-' + MODEL_ID + '_EPOCH0.json', 'w' ) as json_file:
    json_file.write(model_json)
model.save_weights(temp_epoch_dir + 'keras_Model-' + MODEL_ID + '_EPOCH0.h5')


#with open( results_dir + 'keras_Model-' + MODEL_ID + '_history.pkl', 'wb' ) as f:
#   pickle.dump(history.history, f)

a = history.history

for i in np.arange(1,HOW_MANY_SUB_EPOCHS):
    json_file = open(temp_epoch_dir + 'keras_Model-' + MODEL_ID + '_EPOCH' + str(i-1) + '.json','r')
    loaded_model_json = json_file.read()
    json_file.close()
    model = model_from_json(loaded_model_json)
    model.load_weights(temp_epoch_dir + 'keras_Model-' + MODEL_ID + '_EPOCH' + str(i-1) + '.h5')

    adam = Adam(lr = LEARNING_RATE)
    model.compile(loss=bce_dice_loss, optimizer=adam, metrics=[dice_coef,'accuracy','mse'])
    print('Main Epoch: ' + str(i+1) + '/'+str(HOW_MANY_SUB_EPOCHS))

    history = model.fit_generator(training_generator,
                                steps_per_epoch = (len(partition['train'])*PATCH_PER_CASE)//(BATCH_SIZE),
                                validation_data = validation_generator,
                                validation_steps = (len(partition['validation'])*PATCH_PER_CASE)//(BATCH_SIZE),
                                epochs = SUB_EPOCHS,
                                verbose = 1)
    
    #model.save(temp_epoch_dir+'EPOCH_'+str(i)+'.h5')
    model_json = model.to_json()
    with open( temp_epoch_dir + 'keras_Model-' + MODEL_ID + '_EPOCH' + str(i) + '.json', 'w' ) as json_file:
        json_file.write(model_json)
    model.save_weights(temp_epoch_dir + 'keras_Model-' + MODEL_ID + '_EPOCH' + str(i) + '.h5')

    #with open( results_dir + 'keras_Model-' + MODEL_ID + '_history.pkl', 'rb' ) as f:
    #   temp_history = pickle.load(f)

    #new_history=history.history
    a['loss'].extend(history.history['loss'])
    a['mean_squared_error'].extend(history.history['mean_squared_error'])
    a['dice_coef'].extend(history.history['dice_coef'])
    a['val_loss'].extend(history.history['val_loss'])
    a['val_mean_squared_error'].extend(history.history['val_mean_squared_error'])
    a['val_dice_coef'].extend(history.history['val_dice_coef'])
    print(a)

with open( results_dir + 'keras_Model-' + MODEL_ID + '_history.pkl', 'wb' ) as f:
    pickle.dump(a, f)

print('\n -----------------------MODEL FIT SUCCESSFULLY!!!------------------------------')

print('\n -----------------------Starting to write the model!!!------------------------------')
model.save( results_dir + 'keras_Model-' + MODEL_ID + '.h5' )
print('\n -----------------------MODEL WRITTEN as : ' + results_dir + 'keras_Model-' + MODEL_ID + '.h5' + '!!!------------------------------')

print('\n -----------------------Starting to write the history as a pickle!!!------------------------------')
#with open( results_dir + 'keras_Model-' + MODEL_ID + '_history.pkl', 'wb' ) as f:
#   pickle.dump(history.history, f)
print('\n -----------------------HISTORY WRITTEN as : ' + results_dir + 'keras_Model-' + MODEL_ID + '_history.pkl' + '!!!------------------------------')


