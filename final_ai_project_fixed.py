import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# NLP
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
# 1. EHR (RAG + T5 FIXED)
# ==========================================
def ehr_module():
    print("\n===== EHR MODULE =====")

    docs = [
        "Patient has diabetes and hypertension.",
        "Blood pressure is high.",
        "No cardiac illness."
    ]

    reference = "Patient has diabetes and high blood pressure."

    # Embedding
    embed = SentenceTransformer('all-MiniLM-L6-v2')
    vectors = embed.encode(docs)

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(np.array(vectors))

    query = "patient condition"
    q_vec = embed.encode([query])

    _, I = index.search(np.array(q_vec), k=2)
    retrieved = " ".join([docs[i] for i in I[0]])

    # T5 (NO pipeline)
    tokenizer = AutoTokenizer.from_pretrained("t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")

    inputs = tokenizer("summarize: " + retrieved, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=40)

    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

    scorer = rouge_scorer.RougeScorer(['rouge1'], use_stemmer=True)
    rouge = scorer.score(reference, summary)['rouge1'].fmeasure

    print("Summary:", summary)
    print("ROUGE Score:", rouge)

    return rouge


# ==========================================
# 2. LEGAL (GPT)
# ==========================================
def legal_module():
    print("\n===== LEGAL MODULE =====")

    template = "Agreement between client and company."

    generator = pipeline("text-generation", model="distilgpt2")
    ai = generator("Draft a legal agreement:", max_length=80)[0]['generated_text']

    print("Template:", template)
    print("AI Output:", ai)

    return len(template), len(ai)


# ==========================================
# 3. FRAUD (SMOTE vs GAN)
# ==========================================
class Generator(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(10, 16),
            nn.ReLU(),
            nn.Linear(16, 5)
        )

    def forward(self, x):
        return self.net(x)


class Discriminator(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(5, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.net(x)


def fraud_module():
    print("\n===== FRAUD MODULE =====")

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

    loss_fn = nn.BCELoss()
    opt_G = torch.optim.Adam(G.parameters(), lr=0.001)
    opt_D = torch.optim.Adam(D.parameters(), lr=0.001)

    real = torch.randn(100, 5)

    for _ in range(20):
        noise = torch.randn(100, 10)
        fake = G(noise)

        real_label = torch.ones(100, 1)
        fake_label = torch.zeros(100, 1)

        loss_D = loss_fn(D(real), real_label) + loss_fn(D(fake.detach()), fake_label)
        opt_D.zero_grad(); loss_D.backward(); opt_D.step()

        loss_G = loss_fn(D(fake), real_label)
        opt_G.zero_grad(); loss_G.backward(); opt_G.step()

    synthetic = G(torch.randn(200, 10)).detach().numpy()

    X_aug = np.vstack((X_train, synthetic))
    y_aug = np.hstack((y_train, np.ones(len(synthetic))))

    model2 = RandomForestClassifier()
    model2.fit(X_aug, y_aug)
    pred2 = model2.predict(X_test)
    f1_gan = f1_score(y_test, pred2)

    print("F1 SMOTE:", f1_smote)
    print("F1 GAN:", f1_gan)

    return f1_smote, f1_gan


# ==========================================
# 4. BIAS
# ==========================================
def bias_module():
    print("\n===== BIAS MODULE =====")

    generator = pipeline("text-generation", model="distilgpt2")

    std = [len(generator("The doctor said", max_length=20)[0]['generated_text']) for _ in range(5)]
    ctrl = [len(generator("The doctor (neutral) said", max_length=20)[0]['generated_text']) for _ in range(5)]

    var_std = np.var(std)
    var_ctrl = np.var(ctrl)

    print("Standard Variance:", var_std)
    print("Controlled Variance:", var_ctrl)

    return var_std, var_ctrl


# ==========================================
# FINAL RESULTS
# ==========================================
def results(ehr, legal, fraud, bias):
    df = pd.DataFrame({
        "Module": ["EHR", "Legal", "Fraud", "Bias"],
        "Baseline": [0.48, legal[0], fraud[0], bias[0]],
        "Proposed": [ehr, legal[1], fraud[1], bias[1]]
    })

    print("\n===== FINAL RESULTS =====")
    print(df)

    df.to_csv("results.csv", index=False)
    print("\nSaved as results.csv")

    x = np.arange(4)
    plt.bar(x-0.2, df["Baseline"], 0.4, label="Baseline")
    plt.bar(x+0.2, df["Proposed"], 0.4, label="Proposed")
    plt.xticks(x, df["Module"])
    plt.legend()
    plt.title("AI Model Comparison")
    plt.show()


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    ehr = ehr_module()
    legal = legal_module()
    fraud = fraud_module()
    bias = bias_module()

    results(ehr, legal, fraud, bias)