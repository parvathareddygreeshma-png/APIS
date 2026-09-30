from flask import Flask, request, render_template_string
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>QueryFlow</title>
</head>
<body>

<h1>QueryFlow - Intelligent Query Processing System</h1>

<h3>Upload CSV File</h3>
<form action="/upload" method="post" enctype="multipart/form-data">
    <input type="file" name="file">
    <input type="submit" value="Upload">
</form>

<hr>

<h3>Enter SQL Query</h3>
<form action="/query" method="post">
    <input type="text" name="query" size="70"
    value="SELECT * FROM data">
    <input type="submit" value="Execute">
</form>

<br>

<a href="/chart">Generate Chart</a>

<br><br>

{{result|safe}}

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():

    file = request.files['file']

    df = pd.read_csv(file)

    conn = sqlite3.connect('project.db')

    df.to_sql('data', conn, if_exists='replace', index=False)

    conn.close()

    return render_template_string(
        HTML,
        result="<h3>Dataset Uploaded Successfully</h3>"
    )

@app.route('/query', methods=['POST'])
def query():

    sql = request.form['query']

    try:
        conn = sqlite3.connect('project.db')

        df = pd.read_sql_query(sql, conn)

        conn.close()

        return render_template_string(
            HTML,
            result=df.to_html()
        )

    except Exception as e:

        return render_template_string(
            HTML,
            result=f"<h3>Error: {e}</h3>"
        )

@app.route('/chart')
def chart():

    conn = sqlite3.connect('project.db')

    df = pd.read_sql_query(
        "SELECT * FROM data",
        conn
    )

    conn.close()

    num_cols = df.select_dtypes(include='number').columns

    if len(num_cols) > 0:

        plt.figure(figsize=(6,4))

        df[num_cols[0]].value_counts().plot(kind='bar')

        if not os.path.exists("static"):
            os.makedirs("static")

        plt.savefig("static/chart.png")

        plt.close()

        return """
        <h2>Visualization</h2>
        <img src='/static/chart.png'>
        <br><br>
        <a href='/'>Back</a>
        """

    return "No Numeric Column Found"

if __name__ == '__main__':
    app.run(debug=True)
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>QueryFlow</title>

<style>

body{
font-family:Arial, sans-serif;
background:#f4f6f9;
margin:0;
}

.header{
background:#007bff;
color:white;
padding:20px;
text-align:center;
}

.container{
width:80%;
margin:auto;
margin-top:30px;
}

.card{
background:white;
padding:20px;
margin-bottom:20px;
border-radius:10px;
box-shadow:0px 2px 10px rgba(0,0,0,0.2);
}

input[type=file],
input[type=text]{
width:100%;
padding:10px;
margin-top:10px;
}

input[type=submit]{
background:#007bff;
color:white;
border:none;
padding:10px 20px;
border-radius:5px;
cursor:pointer;
}

input[type=submit]:hover{
background:#0056b3;
}

table{
width:100%;
border-collapse:collapse;
}

table,th,td{
border:1px solid #ddd;
padding:8px;
}

th{
background:#007bff;
color:white;
}

</style>

</head>

<body>

<div class="header">
<h1>QueryFlow</h1>
<p>Intelligent Query Processing and Data Analytics System</p>
</div>

<div class="container">

<div class="card">
<h2>Upload Dataset</h2>

<form action="/upload" method="post" enctype="multipart/form-data">
<input type="file" name="file" required>
<br><br>
<input type="submit" value="Upload Dataset">
</form>

</div>

<div class="card">

<h2>Enter SQL Query</h2>

<form action="/query" method="post">

<input type="text"
name="query"
value="SELECT * FROM data">

<br><br>

<input type="submit"
value="Execute Query">

</form>

</div>

<div class="card">

<h2>Generate Visualization</h2>

<a href="/chart">
<input type="submit" value="Generate Chart">
</a>

</div>

<div class="card">

<h2>Results</h2>

{{result|safe}}

</div>

</div>

</body>
</html>
"""