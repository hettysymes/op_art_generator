print("Importing start")

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing import image

print("Importing finished")

# Load model
base_model = VGG16(weights='imagenet')
model = Model(inputs=base_model.input, outputs=base_model.get_layer('fc1').output)


def extract_features(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_data = image.img_to_array(img)
    img_data = np.expand_dims(img_data, axis=0)
    img_data = preprocess_input(img_data)
    features = model.predict(img_data)
    return features.flatten()


artworks = ['movement_in_squares', 'hesitate', 'straight_curve', 'arrest_2', 'conversation', 'blaze', 'shadow_play',
            'blaze_study', 'arrest_1', 'rise_2', 'cataract_3', 'breathe']


def get_similarity(artwork1, artwork2):
    # Extract features from both artworks
    features1 = extract_features(artwork1)
    features2 = extract_features(artwork2)

    # Compute cosine similarity
    similarity = cosine_similarity([features1], [features2])[0][0]
    similarity_percent = similarity * 100

    return similarity_percent


for artwork in artworks:
    similarity_percent = get_similarity(f'evaluation/originals/{artwork}.png', f'evaluation/recreations/{artwork}.png')
    print(f"Similarity for {artwork}: {similarity_percent:.2f}%")
