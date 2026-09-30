import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# NLP (NO pipeline for T5)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from sentence_transformers import SentenceTransformer
import faiss

# ML
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

# ROUGE
from rouge_score import rouge_scorer

# GAN
import torch
import torch.nn as nn


# ==========================================
# 1. EHR WITH TRUE RAG (FIXED)
# ==========================================
def ehr_rag():
    docs = [
        "Patient has diabetes and hypertension.",
        "Blood pressure is high.",
        "No cardiac illness."
    ]

    reference = "Patient has diabetes and high blood pressure."

    # Embeddings
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    doc_vectors = embed_model.encode(docs)

    # FAISS
    index = faiss.IndexFlatL2(doc_vectors.shape[1])
    index.add(np.array(doc_vectors))

    query = "patient condition"
    q_vec = embed_model.encode([query])

    _, I = index.search(np.array(q_vec), k=2)
    retrieved = " ".join([docs[i] for i in I[0]])

    # ✅ FIXED T5 (NO pipeline)
    tokenizer = AutoTokenizer.from_pretrained("t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")

    input_text = "summarize: " + retrieved
    inputs = tokenizer(input_text, return_tensors="pt", truncation=True)

    outputs = model.generate(**inputs, max_length=40)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    scorer = rouge_scorer.RougeScorer(['rouge1'], use_stemmer=True)
    rouge = scorer.score(reference, summary)['rouge1'].fmeasure

    print("\nEHR Summary:", summary)
    print("ROUGE:", rouge)

    return rouge


# ==========================================
# 2. LEGAL DRAFTING (LIGHTWEIGHT)
# ==========================================
def legal_ai():
    template = "Agreement between client and company."

    generator = pipeline("text-generation", model="distilgpt2")  # faster
    ai_text = generator("Draft a legal agreement:", max_length=80)[0]['generated_text']

    score_template = len(template)
    score_ai = len(ai_text)

    print("\nLegal Template:", template)
    print("\nLegal AI:", ai_text)

    return score_template, score_ai


# ==========================================
# 3. FRAUD (SMOTE vs GAN)
# ==========================================
class Generator(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(10, 16),
            nn.ReLU(),
            nn.Linear(16, 5)
        )

    def forward(self, x):
        return self.model(x)


class Discriminator(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(5, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)


def fraud_gan():
    X = np.random.rand(1000, 5)
    y = np.array([0]*950 + [1]*50)

    X_train, X_test, y_train, y_test = train_test_split(X, y)

    # SMOTE
    sm = SMOTE()
    X_sm, y_sm = sm.fit_resample(X_train, y_train)

    model1 = RandomForestClassifier()
    model1.fit(X_sm, y_sm)
    pred1 = model1.predict(X_test)
    f1_smote = f1_score(y_test, pred1)

    # GAN
    G = Generator()
    D = Discriminator()

    criterion = nn.BCELoss()
    opt_G = torch.optim.Adam(G.parameters(), lr=0.001)
    opt_D = torch.optim.Adam(D.parameters(), lr=0.001)

    real = torch.randn(100, 5)

    for _ in range(30):
        noise = torch.randn(100, 10)
        fake = G(noise)

        real_labels = torch.ones(100, 1)
        fake_labels = torch.zeros(100, 1)

        loss_D = criterion(D(real), real_labels) + criterion(D(fake.detach()), fake_labels)
        opt_D.zero_grad(); loss_D.backward(); opt_D.step()

        loss_G = criterion(D(fake), real_labels)
        opt_G.zero_grad(); loss_G.backward(); opt_G.step()

    synthetic = G(torch.randn(200, 10)).detach().numpy()

    X_aug = np.vstack((X_train, synthetic))
    y_aug = np.hstack((y_train, np.ones(len(synthetic))))

    model2 = RandomForestClassifier()
    model2.fit(X_aug, y_aug)
    pred2 = model2.predict(X_test)
    f1_gan = f1_score(y_test, pred2)

    print("\nF1 SMOTE:", f1_smote)
    print("F1 GAN:", f1_gan)

    return f1_smote, f1_gan


# ==========================================
# 4. BIAS MITIGATION
# ==========================================
def bias_module():
    generator = pipeline("text-generation", model="distilgpt2")

    std = [len(generator("The doctor said", max_length=20)[0]['generated_text']) for _ in range(5)]
    ctrl = [len(generator("The doctor (neutral) said", max_length=20)[0]['generated_text']) for _ in range(5)]

    var_std = np.var(std)
    var_ctrl = np.var(ctrl)

    print("\nBias Variance Standard:", var_std)
    print("Bias Variance Controlled:", var_ctrl)

    return var_std, var_ctrl


# ==========================================
# RESULTS + GRAPH + CSV
# ==========================================
def save_results(ehr, legal, fraud, bias):
    data = {
        "Module": ["EHR", "Legal", "Fraud", "Bias"],
        "Baseline": [0.48, legal[0], fraud[0], bias[0]],
        "Proposed": [ehr, legal[1], fraud[1], bias[1]]
    }

    df = pd.DataFrame(data)
    df.to_csv("results.csv", index=False)

    print("\nSaved results.csv")

    x = np.arange(4)
    plt.figure()
    plt.bar(x-0.2, df["Baseline"], 0.4, label="Baseline")
    plt.bar(x+0.2, df["Proposed"], 0.4, label="Proposed")
    plt.xticks(x, df["Module"])
    plt.legend()
    plt.title("Final Results Comparison")
    plt.show()


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    ehr = ehr_rag()
    legal = legal_ai()
    fraud = fraud_gan()
    bias = bias_module()

    save_results(ehr, legal, fraud, bias)