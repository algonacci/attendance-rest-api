import tensorflow as tf
import numpy as np
from keras.models import load_model

model = load_model("model.h5")

class_names = ['bagas', 'davin', 'joshua', 'kevin', 'puan', 'rere', 'taufiq']


def predict(img):
    img_array = tf.keras.preprocessing.image.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)
    predictions = model.predict(img_array)
    predicted_class = class_names[np.argmax(predictions[0])]
    confidence = round(100 * (np.max(predictions[0])), 2)
    return predicted_class, confidence
