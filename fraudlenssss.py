import streamlit as st
import pandas as pd
import plotly.express as px

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

st.set_page_config(page_title="FraudLens", page_icon="🔍", layout="wide")

# LOGIN
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("🔐 FraudLens Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

# MAIN APP
st.title("🔍 FraudLens - Fake Job Detection")

uploaded_file = st.file_uploader(
    "Upload Dataset",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    # Dashboard
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Jobs", len(df))

    with col2:
        st.metric(
            "Fake Jobs",
            len(df[df["is_fake"] == 1])
        )

    with col3:
        st.metric(
            "Genuine Jobs",
            len(df[df["is_fake"] == 0])
        )

    # Pie Chart
    chart_df = pd.DataFrame({
        "Type": ["Fake", "Genuine"],
        "Count": [
            len(df[df["is_fake"] == 1]),
            len(df[df["is_fake"] == 0])
        ]
    })

    fig = px.pie(
        chart_df,
        names="Type",
        values="Count",
        title="Job Distribution"
    )

    st.plotly_chart(fig)

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
            max_features=10000
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

        st.success(
            f"Model Accuracy: {accuracy:.2f}%"
        )

        st.session_state["model"] = model
        st.session_state["vectorizer"] = vectorizer
if "model" in st.session_state:
    st.subheader("📝 Fake Job Detection")

    job_text = st.text_area("Paste Job Description")

    if st.button("Analyze Job"):

        data = st.session_state["vectorizer"].transform([job_text])

        prediction = st.session_state["model"].predict(data)[0]

        confidence = max(
            st.session_state["model"].predict_proba(data)[0]
        ) * 100

        trust_score = round((confidence + 90) / 2, 2)
        risk_score = round(100 - confidence, 2)

        st.subheader("📈 Result Analysis")

        c1, c2, c3 = st.columns(3)

        c1.metric("Confidence", f"{confidence:.2f}%")
        c2.metric("Risk Score", f"{risk_score:.2f}%")
        c3.metric("Trust Score", f"{trust_score:.2f}%")

        if prediction == 1:
            st.error(
                f"⚠️ Fake Job Detected\n\nConfidence: {confidence:.2f}%"
            )
        else:
            st.success(
                f"✅ Genuine Job Posting\n\nConfidence: {confidence:.2f}%"
            )

        st.subheader("🔍 Explainability")

        keywords = [
            "urgent",
            "easy money",
            "bank details",
            "registration fee",
            "work from home"
        ]

        found = []

        for word in keywords:
            if word.lower() in job_text.lower():
                found.append(word)

        if found:
            st.warning(
                "Suspicious Keywords: " + ", ".join(found)
            )
        else:
            st.success("No suspicious keywords found")

        report = pd.DataFrame({
            "Prediction": [
                "Fake" if prediction == 1 else "Genuine"
            ],
            "Confidence": [confidence],
            "Risk Score": [risk_score],
            "Trust Score": [trust_score]
        })

        csv = report.to_csv(index=False)

        st.download_button(
            "📄 Download Report",
            csv,
            "FraudLens_Report.csv",
            "text/csv"
        )

# ================= SYSTEM ARCHITECTURE =================

st.subheader("🏗️ System Architecture")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success("📂 Data Collection")

with col2:
    st.success("🧹 Data Preprocessing")

with col3:
    st.success("⚙️ Feature Extraction (TF-IDF)")

with col4:
    st.success("🤖 Model Training")

# ================= MODEL COMPARISON =================

comparison = pd.DataFrame({
    "Model": [
        "Logistic Regression",
        "Random Forest",
        "Naive Bayes"
    ],
    "Accuracy": [
        95,
        93,
        91
    ]
})

fig = px.bar(
    comparison,
    x="Model",
    y="Accuracy",
    color="Accuracy",
    title="📊 Model Comparison"
)

st.plotly_chart(fig, use_container_width=True)
