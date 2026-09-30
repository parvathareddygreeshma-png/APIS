import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# Load Dataset
print("Loading Dataset...")

df = pd.read_csv("fake_job_postings.csv")

# Fill Missing Values
df = df.fillna('')

# Combine Important Text Columns
df["combined_text"] = (
    df["title"] + " " +
    df["company_profile"] + " " +
    df["description"] + " " +
    df["requirements"] + " " +
    df["benefits"]
)

# Features and Target
X = df["combined_text"]
y = df["fraudulent"]

# Split Dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Convert Text to Numerical Features
vectorizer = TfidfVectorizer(
    stop_words='english',
    max_features=5000
)

X_train = vectorizer.fit_transform(X_train)
X_test = vectorizer.transform(X_test)

# Train Model
print("Training Model...")

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Test Accuracy
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nModel Accuracy:", round(accuracy * 100, 2), "%")

# User Input Section
print("\n==============================")
print(" FRAUDLENS - FAKE JOB DETECTOR ")
print("==============================")

while True:

    print("\nPaste Job Description:")
    job_text = input()

    transformed_text = vectorizer.transform([job_text])

    result = model.predict(transformed_text)

    confidence = max(model.predict_proba(transformed_text)[0]) * 100

    if result[0] == 1:
        print("\n⚠️ FAKE JOB DETECTED")
    else:
        print("\n✅ GENUINE JOB POSTING")

    print("Confidence:", round(confidence, 2), "%")

    choice = input("\nCheck another job? (y/n): ")

    if choice.lower() != 'y':
        print("Thank you for using FraudLens!")
        break