# -*- coding: utf-8 -*-
"""Twitter Sentiment Analysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/11MK3lBI2WG2eCDRFxuupdFuqhqpponRJ
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers,Model,models
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.layers import Dense,Flatten,Embedding,Activation,Dropout,SpatialDropout1D,Bidirectional,LSTM
from nltk.corpus import stopwords
from string import punctuation
from nltk.stem import WordNetLemmatizer, SnowballStemmer, PorterStemmer
import matplotlib.pyplot as plt
from nltk.tag import pos_tag
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.optimizers import Adam

import nltk
import subprocess

# Download and unzip wordnet
try:
    nltk.data.find('wordnet.zip')
except:
    nltk.download('wordnet', download_dir='/kaggle/working/')
    command = "unzip /kaggle/working/corpora/wordnet.zip -d /kaggle/working/corpora"
    subprocess.run(command.split())
    nltk.data.path.append('/kaggle/working/')

# Now you can import the NLTK resources as usual
from nltk.corpus import wordnet

nltk.download('stopwords')
nltk.download('wordnet')

wnl = WordNetLemmatizer()
stemmer = SnowballStemmer('english')
porter_stemmer = PorterStemmer()
all_stopwords = set(stopwords.words('english'))
# stemmer = SnowballStemmer("english")
all_stopwords = [w for w in all_stopwords if w not in ['no','not']]


def stemming(tweet):
    words = tweet.split()
    stemmed_words = [wnl.lemmatize(word) for word in words if word not in all_stopwords]
    # stemmed_words = [porter_stemmer.stem(word) for word in words if word not in all_stopwords]
    return ' '.join(stemmed_words)

!pip install spacy
!python -m spacy download en_core_web_sm

import spacy

nlp =spacy.load("en_core_web_sm")

col=["id","country","label","text"]
df_train=pd.read_csv("/content/twitter_training.csv",names=col)
df_test=pd.read_csv("/content/twitter_validation.csv",names=col)

df_train.dropna(inplace=True)

df_train.drop_duplicates(inplace=True)



df_train['text']=df_train['text'].apply(stemming)

df_test['text']=df_test['text'].apply(stemming)

def text_cleaner(text):
    # Convert to lowercase
    text = text.lower()

    # Replace contractions and abbreviations
    contractions = {
        r"won't": "will not",
        r"can't": "cannot",
        r"n't": " not",
        r"'re": " are",
        r"'s": " is",
        r"'d": " would",
        r"'ll": " will",
        r"'t": " not",
        r"'ve": " have",
        r"'m": " am",
        r"im": "i am",
        r"don't": "do not",
        r"shouldn't": "should not",
        r"needn't": "need not",
        r"hasn't": "has not",
        r"haven't": "have not",
        r"weren't": "were not",
        r"mightn't": "might not",
        r"didn't": "did not"
    }
    for pattern, replacement in contractions.items():
        text = re.sub(pattern, replacement, text)

    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', ' ', text, flags=re.MULTILINE)

    # Remove emojis and non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)

    # Remove punctuation and special characters (except !, ?, ., @)
    text = re.sub(r'[^a-zA-Z0-9\!\?\.\@\s]', ' ', text)

    # Remove numbers
    text = re.sub(r'\d+', ' ', text)

    # Normalize repeated punctuation
    text = re.sub(r'[!]+', '!', text)
    text = re.sub(r'[?]+', '?', text)
    text = re.sub(r'[.]+', '.', text)
    text = re.sub(r'[@]+', '@', text)

    # Remove extra spaces and newlines
    text = re.sub(r'\s+', ' ', text).strip()

    return text

df_train['text']=df_train['text'].apply(text_cleaner)

df_test['text']=df_test['text'].apply(text_cleaner)

df_train["label"].value_counts()

df_train = df_train[df_train['label'].isin(['Negative', 'Positive', 'Neutral'])]

df_test = df_test[df_test['label'].isin(['Negative', 'Positive', 'Neutral'])]

import matplotlib.pyplot as plt

# Count the number of occurrences of each label
label_counts = df_train['label'].value_counts()

# Create a pie chart
plt.figure(figsize=(6, 6))
plt.pie(
    label_counts,
    labels=label_counts.index,
    autopct='%1.1f%%',
    colors=['skyblue', 'lightgreen', 'lightcoral'],
    startangle=90
)
plt.title('Sentiment Label Distribution in Training Data')
plt.show()



# Encode labels
label_mapping = {'Negative': 0, 'Neutral': 1, 'Positive': 2}
df_train['label_encoded'] = df_train['label'].map(label_mapping)
df_test['label_encoded'] = df_test['label'].map(label_mapping)

df_training = df_train[['text', 'label_encoded']].copy()
df_validation = df_test[['text','label_encoded']].copy()

from tensorflow.keras import models, layers
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

tokenizer = Tokenizer(oov_token="<OOV>")
tokenizer.fit_on_texts(df_training['text'])

# Convert text data to sequences of integers
train_sequences = tokenizer.texts_to_sequences(df_training['text'])
valid_sequences = tokenizer.texts_to_sequences(df_validation['text'])

# Pad sequences
maxlength = 100  # Adjust based on your dataset
X_train = pad_sequences(train_sequences, maxlen=maxlength)
X_valid = pad_sequences(valid_sequences, maxlen=maxlength)
vocab_size = len(tokenizer.word_index) + 1  # +1 for padding token

model = models.Sequential([
    layers.Embedding(input_dim=vocab_size, output_dim=200, input_length=maxlength),
    layers.Bidirectional(layers.LSTM(128, return_sequences=True)),
    layers.Bidirectional(layers.LSTM(64)),
    layers.Dropout(0.3),
    layers.Dense(32, activation='relu'),
    layers.Dropout(0.3),
    layers.Dense(3, activation='softmax')  # Assuming 3 classes
])

# Compile the model
opt = Adam(learning_rate=0.001)  # Start with a lower learning rate
model.compile(
    optimizer=opt,
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

# Train the model
history = model.fit(
    X_train, df_training['label_encoded'],
    validation_data=(X_valid, df_validation['label_encoded']),
    epochs=20,
    batch_size=512,
    verbose=1
)

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper right')
plt.show()


# Plot the accuracy of training and validation
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='lower right')
plt.show()

