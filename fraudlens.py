import streamlit as st
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="FraudLens", page_icon="🔍", layout="wide")

st.title("🔍 FraudLens - Fake Job Detection")

uploaded_file = st.file_uploader(
    "Upload fake_real_job_postings_3000x25.csv",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    if st.button("Train Model"):

        df = df.fillna("")

        df["text"] = (
            df["job_title"].astype(str) + " " +
            df["job_description"].astype(str) + " " +
            df["requirements"].astype(str) + " " +
            df["benefits"].astype(str) + " " +
            df["company_profile"].astype(str) + " " +
            df["industry"].astype(str)
        )

        X = df["text"]
        y = df["is_fake"]

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )

        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=10000,
            ngram_range=(1, 2)
        )

        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)

        model = LogisticRegression(max_iter=3000)

        model.fit(X_train_vec, y_train)

        predictions = model.predict(X_test_vec)

        accuracy = accuracy_score(
            y_test,
            predictions
        ) * 100

        st.session_state["model"] = model
        st.session_state["vectorizer"] = vectorizer

        st.success(
            f"Model Trained Successfully! Accuracy: {accuracy:.2f}%"
        )

if "model" in st.session_state:

    st.markdown("---")

    st.subheader("Analyze Job Posting")

    job_text = st.text_area(
        "Paste Job Description Here"
    )

    if st.button("Analyze Job"):

        vectorizer = st.session_state["vectorizer"]
        model = st.session_state["model"]

        data = vectorizer.transform([job_text])

        prediction = model.predict(data)[0]

        confidence = max(
            model.predict_proba(data)[0]
        ) * 100

        risk_score = round(100 - confidence, 2)
        trust_score = round((confidence + 90) / 2, 2)

        if prediction == 1:
            st.error(
                f"⚠️ Fake Job Detected\n\nConfidence: {confidence:.2f}%"
            )
        else:
            st.success(
                f"✅ Genuine Job Posting\n\nConfidence: {confidence:.2f}%"
            )

        c1, c2, c3 = st.columns(3)

        c1.metric("Confidence", f"{confidence:.2f}%")
        c2.metric("Risk Score", f"{risk_score}%")
        c3.metric("Trust Score", f"{trust_score}%")
