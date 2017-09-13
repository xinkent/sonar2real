import numpy as np
import keras
from keras import backend as K
from keras.models import Sequential, Model
from keras.layers import Dense,Reshape, Input,merge
from keras.layers.merge import concatenate
from keras.layers.core import Activation, Dropout, Flatten,Lambda
from keras.layers.normalization import BatchNormalization
from keras.layers.convolutional import UpSampling2D,Conv2D, MaxPooling2D,Conv2DTranspose
from keras.layers.advanced_activations import LeakyReLU

# convolution batchnormalization relu
def CBR(ch,shape,bn=True,sample='down',activation=LeakyReLU, dropout=False):
    model = Sequential()
    if sample=='down':
        model.add(Conv2D(filters=ch, kernel_size=(4,4), strides=2, padding='same',input_shape=shape))
    else:
        model.add(Conv2DTranspose(filters=ch, kernel_size=(4,4), strides=2, padding='same',input_shape=shape))
    if bn:
        model.add(BatchNormalization())
    if dropout:
        model.add(Dropout(0.5))
    if activation == LeakyReLU:
        model.add(LeakyReLU(alpha=0.2))
    else:
        model.add(Activation('relu'))

    return model



def discriminator():
    h = 512
    w = 256
    gen_output = Input(shape=(h,w,3))
    label_input = Input(shape=(h,w,1))
    x1 = CBR(32,(512,256,1), bn=False)(label_input)
    x2 = CBR(32,(256,128,3),bn=False)(gen_output)
    x = concatenate([x1,x2])
    x = CBR(128,(128,64,64))(x)
    x = CBR(256,(64,32,128))(x)
    x = CBR(512,(32,16,256))(x)
    x = Conv2D(filters=1,kernel_size=3,strides=1,padding='same')(x)
    x = Activation('softplus')(x)
    output = Lambda(lambda x: K.mean(x, axis=[1,2]),output_shape=(1,))(x)
    model = Model(inputs =[label_input,gen_output], outputs = [output])

    return model


def generator():

    # encoder
    input1 = Input(shape=(512,256,1))
    enc_1 = Conv2D(filters=64, kernel_size=(3,3), strides=1, padding='same',input_shape=(256,256,1))(input1)
    enc_2 = CBR(128,(512,256,64))(enc_1)
    enc_3 = CBR(256,(256,128,128))(enc_2)
    enc_4 = CBR(512,(128,64,256))(enc_3)
    enc_5 = CBR(512,(64,32,512))(enc_4)
    enc_6 = CBR(512,(32,16,512))(enc_5)
    enc_7 = CBR(512,(16,8,512))(enc_6)
    enc_8 = CBR(512,(8,4,512))(enc_7)

    # decoder
    x = CBR(512,(4,2,512),sample='up',activation='relu',dropout=True)(enc_8)
    x = CBR(512,(8,4,1024),sample='up',activation='relu',dropout=True)(concatenate([x,enc_7]))
    x = CBR(512,(16,8,1024),sample='up',activation='relu',dropout=True)(concatenate([x,enc_6]))
    x = CBR(512,(32,16,1024),sample='up',activation='relu',dropout=False)(concatenate([x,enc_5]))
    x = CBR(256,(64,32,1024),sample='up',activation='relu',dropout=False)(concatenate([x,enc_4]))

    x = CBR(128,(128,64,512),sample='up',activation='relu',dropout=False)(concatenate([x,enc_3]))
    x = CBR(64,(256,128,256),sample='up',activation='relu',dropout=False)(concatenate([x,enc_2]))
    output = Conv2D(filters=3, kernel_size=(3,3),strides=1,padding="same")(concatenate([x,enc_1]))

    model = Model(inputs=input1, outputs=output)
    return(model)


def GAN(generator, discriminator):

    gen_input = Input(shape=(512,256,1))
    img_input = Input(shape=(512,256,3))

    generated_image = generator(gen_input)
    DCGAN_output = discriminator([gen_input,img_input])

    DCGAN = Model(inputs=[gen_input,img_input],outputs=[generated_image, DCGAN_output],name="DCGAN")

    return DCGAN
