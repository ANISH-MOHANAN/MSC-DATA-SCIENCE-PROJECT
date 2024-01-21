import os
import pickle
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import numpy as np
import sys

def train_svm_model():    
    try:
        pickle_file_path = os.path.join('dataset', 'data.pickle')
        data_dict = pickle.load(open(pickle_file_path, 'rb'))
    except FileNotFoundError:
        print("Error: data.pickle file not found. Training failed.", file=sys.stderr)
        sys.exit(1)

    # Check if the 'data' and 'labels' are in the expected format
    if not all(isinstance(sample, np.ndarray) for sample in data_dict['data']):
        print("Error: 'data' should contain only arrays. Training failed.", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data_dict['labels'], np.ndarray):
        print("Error: 'labels' should be a numpy array. Training failed.", file=sys.stderr)
        sys.exit(1)

    data = np.vstack(data_dict['data']) 
    labels = np.asarray(data_dict['labels'])

    if len(data) == 0 or len(labels) == 0:
        print("Error: Empty data or labels. Training failed.", file=sys.stderr)
        sys.exit(1)

    # Check the shapes of 'data' and 'labels' before concatenation
    print("Data shape before concatenation:", data_dict['data'][0].shape)
    print("Labels shape before concatenation:", labels.shape)

    # Check if the number of samples in 'data' matches the number of samples in 'labels'
    if len(data) != len(labels):
        print("Error: Inconsistent number of samples between data and labels. Training failed.", file=sys.stderr)
        sys.exit(1)

    # Check the shapes of 'data' and 'labels' after concatenation
    print("Data shape after concatenation:", data.shape)
    print("Labels shape after concatenation:", labels.shape)

    x_train, x_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, shuffle=True, stratify=labels)

    if len(np.unique(y_train)) <= 1:
        print("Error: Insufficient number of classes. Training failed.", file=sys.stderr)
        sys.exit(1)

    model = SVC(kernel='linear')  # You can choose different kernels (e.g., 'linear', 'rbf', 'poly', etc.)

    model.fit(x_train, y_train)

    # Evaluate the model on the test dataset
    y_predict = model.predict(x_test)
    test_score = accuracy_score(y_predict, y_test)
    print('Accuracy on Test Dataset: {:.2f}%'.format(test_score * 100))

    # Perform cross-validation and calculate the mean and standard deviation of scores
    cv_scores = cross_val_score(model, data, labels, cv=5)
    mean_cv_score = cv_scores.mean()
    std_cv_score = cv_scores.std()
    print("Cross-Validation Scores:", cv_scores)
    print("Mean Cross-Validation Score:", mean_cv_score)
    print("Standard Deviation of Cross-Validation Score:", std_cv_score)

    model_folder = 'model'
    os.makedirs(model_folder, exist_ok=True)
    model_file_path = os.path.join(model_folder, 'svm_model.p')
    with open(model_file_path, 'wb') as f:
        pickle.dump({'model': model}, f)

    print('Training completed. SVM model saved.')

if __name__ == '__main__':
    try:
        train_svm_model()
    except Exception as e:
        print("Error:", str(e), file=sys.stderr)
        sys.exit(1)
