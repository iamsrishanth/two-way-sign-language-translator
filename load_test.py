
import os

# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

try:
    print("Attempting to load model with tf_keras...")
    from tf_keras.models import load_model
    model = load_model('model.h5')
    print("SUCCESS: Model loaded successfully with tf_keras.")
    model.summary()
except Exception as e:
    print(f"FAILURE: An error occurred: {e}")
    exit(1)
