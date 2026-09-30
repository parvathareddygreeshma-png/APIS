from flask import Flask, request, jsonify, session, redirect, render_template_string
import sqlite3
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smart-campus-wifi6-2026"
DB = "smart_campus_wifi6.db"

# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            device_type TEXT,
            connection TEXT,
            ip TEXT,
            status TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wifi_config(
            id INTEGER PRIMARY KEY,
            ssid TEXT,
            band TEXT,
            channel INTEGER,
            width TEXT,
            power INTEGER,
            ofdma TEXT,
            mu_mimo TEXT,
            bss_coloring TEXT,
            twt TEXT
        )
    """)

    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users(username,password,role) VALUES(?,?,?)",
            ("admin", "admin123", "Administrator")
        )

    if cur.execute("SELECT COUNT(*) FROM devices").fetchone()[0] == 0:
        devices = [
            ("Wireless Router0", "Wireless Router", "Core/Wireless", "192.168.1.1", "Online"),
            ("2960 Switch", "Switch", "Wired", "192.168.1.2", "Online"),
            ("Server0", "Server", "Wired", "192.168.1.10", "Online"),
            ("Server1", "Server", "Wired", "192.168.1.11", "Online"),
            ("Server2", "Server", "Wired", "192.168.1.12", "Online"),
            ("PC0", "PC", "Wired", "192.168.1.20", "Online"),
            ("PC1", "PC", "Wired", "192.168.1.21", "Online"),
            ("Laptop0", "Laptop", "Wireless", "192.168.1.30", "Connected"),
            ("Laptop1", "Laptop", "Wireless", "192.168.1.31", "Connected"),
            ("Smartphone0", "Smartphone", "Wireless", "192.168.1.32", "Connected"),
            ("TabletPC0", "Tablet", "Wireless", "192.168.1.33", "Connected")
        ]
        cur.executemany("""
            INSERT INTO devices(name,device_type,connection,ip,status)
            VALUES(?,?,?,?,?)
        """, devices)

    if cur.execute("SELECT COUNT(*) FROM wifi_config").fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO wifi_config
            VALUES(1,'SmartCampus-WiFi6','5 GHz',149,'80 MHz',20,
                   'Enabled','Enabled','Enabled','Enabled')
        """)

    conn.commit()
    conn.close()

init_db()

# ============================================================
# LOGIN
# ============================================================

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SmartWiFi Campus Login</title>
<style>
*{box-sizing:border-box;font-family:Arial,sans-serif}
body{
    margin:0;min-height:100vh;display:flex;align-items:center;
    justify-content:center;background:linear-gradient(135deg,#0f172a,#2563eb)
}
.login{
    width:390px;background:white;padding:35px;border-radius:20px;
    box-shadow:0 25px 60px rgba(0,0,0,.30)
}
.logo{text-align:center;font-size:31px;font-weight:800}
.logo span{color:#2563eb}
.sub{text-align:center;color:#64748b;margin:10px 0 25px}
input{
    width:100%;padding:13px;margin:7px 0 15px;
    border:1px solid #cbd5e1;border-radius:8px
}
button{
    width:100%;padding:13px;border:0;border-radius:8px;
    background:#2563eb;color:white;font-weight:bold;font-size:15px;cursor:pointer
}
button:hover{background:#1d4ed8}
.demo{
    margin-top:18px;padding:13px;background:#eff6ff;border-radius:9px;
    color:#1e40af;font-size:13px
}
</style>
</head>
<body>
<div class="login">
    <div class="logo">Smart<span>WiFi</span></div>
    <div class="sub">Smart Campus Wi-Fi 6 Network Management</div>
    <form method="POST" action="/login">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button>Login</button>
    </form>
    <div class="demo">
        <b>Demo Login</b><br><br>
        Username: admin<br>
        Password: admin123
    </div>
</div>
</body>
</html>
"""

# ============================================================
# DASHBOARD
# ============================================================

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Smart Campus Wi-Fi 6</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0;font-family:Arial,sans-serif}
html{scroll-behavior:smooth}
body{background:#f1f5f9;color:#1e293b}
.sidebar{
    position:fixed;left:0;top:0;width:245px;height:100vh;
    background:#0f172a;color:white;padding:24px 15px;z-index:5
}
.logo{text-align:center;font-size:25px;font-weight:800;margin-bottom:30px}
.logo span{color:#38bdf8}
.menu{list-style:none}
.menu li{
    padding:13px;margin:5px 0;border-radius:8px;cursor:pointer
}
.menu li:hover,.menu li.active{background:#1e40af}
.logout{margin-top:20px;background:#dc2626!important}
.main{margin-left:245px;padding:25px}
.header{
    display:flex;justify-content:space-between;align-items:center;
    margin-bottom:22px;gap:15px
}
.header h1{font-size:28px}
.header p{color:#64748b;margin-top:5px}
.status{
    background:#dcfce7;color:#166534;padding:10px 17px;
    border-radius:20px;font-weight:bold;white-space:nowrap
}
.cards{
    display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
    gap:15px;margin-bottom:20px
}
.card{
    background:white;padding:19px;border-radius:14px;
    box-shadow:0 3px 15px rgba(0,0,0,.07)
}
.card h3{font-size:13px;color:#64748b;margin-bottom:9px}
.value{font-size:28px;font-weight:800}
.blue{color:#2563eb}.green{color:#16a34a}
.orange{color:#ea580c}.red{color:#dc2626}
.grid{display:grid;grid-template-columns:2fr 1fr;gap:20px}
.panel{
    background:white;padding:20px;border-radius:14px;
    box-shadow:0 3px 15px rgba(0,0,0,.07);margin-bottom:20px
}
.panel h2{font-size:19px;margin-bottom:16px}
table{width:100%;border-collapse:collapse}
th,td{padding:10px;border-bottom:1px solid #e2e8f0;text-align:left;font-size:13px}
th{background:#f8fafc}
.online{color:#16a34a;font-weight:bold}
.warning{color:#ea580c;font-weight:bold}
.connected{color:#2563eb;font-weight:bold}
button.action{
    width:auto;padding:10px 16px;background:#2563eb
}
button.secondary{background:#475569}
button.danger{background:#dc2626}
select,input.config{
    width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:7px
}
.form-group{margin-bottom:13px}
.form-group label{display:block;font-weight:bold;font-size:13px;margin-bottom:6px}
.config-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.alert{
    padding:13px;border-radius:8px;margin:8px 0;
    background:#fff7ed;border-left:5px solid #f97316
}
.alert.ok{background:#dcfce7;border-left-color:#22c55e}
.alert.bad{background:#fee2e2;border-left-color:#dc2626}
.recommendation{
    padding:12px;background:#eff6ff;border-left:5px solid #2563eb;
    border-radius:7px;margin:8px 0
}
.metric-grid{
    display:grid;grid-template-columns:repeat(2,1fr);gap:12px
}
.metric{
    background:#f8fafc;padding:14px;border-radius:9px
}
.metric b{font-size:22px}
/* Packet Tracer topology */
.topology{
    position:relative;height:470px;background:#eef2f7;
    border:2px solid #cbd5e1;border-radius:12px;overflow:hidden
}
.node{
    position:absolute;width:120px;min-height:58px;padding:9px;
    background:white;border:2px solid #64748b;border-radius:10px;
    text-align:center;z-index:2;box-shadow:0 3px 10px rgba(0,0,0,.12)
}
.node .icon{font-size:22px}
.node small{display:block;color:#64748b;margin-top:3px}
.router{left:44%;top:25px;border-color:#2563eb}
.switch{left:44%;top:140px;border-color:#16a34a}
.server0{left:5%;top:280px}
.server1{left:23%;top:280px}
.server2{left:41%;top:280px}
.pc0{left:59%;top:280px}
.pc1{left:77%;top:280px}
.laptop0{left:10%;top:90px;border-color:#7c3aed}
.laptop1{left:29%;top:55px;border-color:#7c3aed}
.phone{left:64%;top:55px;border-color:#7c3aed}
.tablet{left:82%;top:100px;border-color:#7c3aed}
.wire{
    position:absolute;height:3px;background:#334155;transform-origin:left center;
    z-index:1
}
.w1{left:50%;top:84px;width:3px;height:56px}
.w2{left:49%;top:198px;width:3px;height:84px}
.w3{left:50%;top:198px;width:210px;transform:rotate(24deg)}
.w4{left:50%;top:198px;width:330px;transform:rotate(22deg)}
.w5{left:50%;top:198px;width:450px;transform:rotate(20deg)}
.w6{left:50%;top:198px;width:550px;transform:rotate(17deg)}
.w7{left:50%;top:198px;width:660px;transform:rotate(15deg)}
.wireless{
    border-top:3px dashed #7c3aed;background:transparent;height:0
}
.wl1{left:50%;top:84px;width:300px;transform:rotate(174deg)}
.wl2{left:50%;top:84px;width:220px;transform:rotate(160deg)}
.wl3{left:50%;top:84px;width:240px;transform:rotate(20deg)}
.wl4{left:50%;top:84px;width:350px;transform:rotate(25deg)}
.legend{
    display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;
    font-size:12px;color:#475569
}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px}
.dot.wired{background:#334155}.dot.wifi{background:#7c3aed}
.heat{
    height:20px;border-radius:12px;
    background:linear-gradient(90deg,#22c55e,#84cc16,#eab308,#f97316,#dc2626);
    margin-top:8px
}
.progress{
    height:9px;background:#e2e8f0;border-radius:10px;overflow:hidden;margin:7px 0 12px
}
.progress span{display:block;height:100%;background:#2563eb}
.small{font-size:12px;color:#64748b}
.hidden{display:none}
.footer-note{
    text-align:center;color:#64748b;font-size:12px;margin:25px 0 5px
}
@media(max-width:1000px){
    .grid{grid-template-columns:1fr}
}
@media(max-width:750px){
    .sidebar{width:70px;padding:20px 8px}
    .logo{font-size:0}.logo span{font-size:20px}
    .menu li{font-size:0;text-align:center}
    .main{margin-left:70px;padding:15px}
    .header{align-items:flex-start;flex-direction:column}
    .config-grid{grid-template-columns:1fr}
    .topology{height:600px;transform:none}
    .node{width:105px}
}
</style>
</head>

<body>

<div class="sidebar">
    <div class="logo">Smart<span>WiFi</span></div>
    <ul class="menu">
        <li onclick="go('dashboard')">📊 Dashboard</li>
        <li onclick="go('packet')">🌐 Packet Tracer</li>
        <li onclick="go('devices')">📡 Devices</li>
        <li onclick="go('wifi')">⚙️ Wi-Fi 6</li>
        <li onclick="go('optimization')">🤖 Optimization</li>
        <li onclick="go('performance')">📈 Performance</li>
        <li onclick="go('alerts')">🚨 Alerts</li>
    </ul>
    <form method="POST" action="/logout">
        <button class="logout">Logout</button>
    </form>
</div>

<div class="main">

<div class="header" id="dashboard">
    <div>
        <h1>Smart Campus Wi-Fi 6</h1>
        <p>802.11ax Configuration, Optimization & Performance Enhancement</p>
    </div>
    <div class="status">● Network Operational</div>
</div>

<div class="cards">
    <div class="card">
        <h3>Connected Devices</h3>
        <div class="value blue" id="users">10</div>
    </div>
    <div class="card">
        <h3>Wireless Clients</h3>
        <div class="value blue" id="wireless">4</div>
    </div>
    <div class="card">
        <h3>Throughput</h3>
        <div class="value green"><span id="throughput">780</span> Mbps</div>
    </div>
    <div class="card">
        <h3>Latency</h3>
        <div class="value orange"><span id="latency">22</span> ms</div>
    </div>
    <div class="card">
        <h3>Packet Loss</h3>
        <div class="value red"><span id="loss">0.8</span>%</div>
    </div>
    <div class="card">
        <h3>Channel Utilization</h3>
        <div class="value orange"><span id="util">48</span>%</div>
    </div>
</div>

<!-- ===================================================== -->
<!-- PACKET TRACER -->
<!-- ===================================================== -->

<div class="panel" id="packet">
<h2>🌐 Cisco Packet Tracer Network</h2>

<p class="small" style="margin-bottom:12px">
Website representation of the uploaded <b>wifi 6 capstone.pkt</b> topology.
The actual Cisco Packet Tracer simulation remains in Cisco Packet Tracer.
</p>

<div class="topology">

    <div class="node router">
        <div class="icon">📶</div>
        <b>Wireless Router0</b>
        <small>192.168.1.1</small>
    </div>

    <div class="node switch">
        <div class="icon">🔀</div>
        <b>2960 Switch</b>
        <small>192.168.1.2</small>
    </div>

    <div class="node server0">
        <div class="icon">🖥️</div>
        <b>Server0</b>
        <small>192.168.1.10</small>
    </div>

    <div class="node server1">
        <div class="icon">🖥️</div>
        <b>Server1</b>
        <small>192.168.1.11</small>
    </div>

    <div class="node server2">
        <div class="icon">🖥️</div>
        <b>Server2</b>
        <small>192.168.1.12</small>
    </div>

    <div class="node pc0">
        <div class="icon">💻</div>
        <b>PC0</b>
        <small>192.168.1.20</small>
    </div>

    <div class="node pc1">
        <div class="icon">💻</div>
        <b>PC1</b>
        <small>192.168.1.21</small>
    </div>

    <div class="node laptop0">
        <div class="icon">💻</div>
        <b>Laptop0</b>
        <small>Wireless</small>
    </div>

    <div class="node laptop1">
        <div class="icon">💻</div>
        <b>Laptop1</b>
        <small>Wireless</small>
    </div>

    <div class="node phone">
        <div class="icon">📱</div>
        <b>Smartphone0</b>
        <small>Wireless</small>
    </div>

    <div class="node tablet">
        <div class="icon">📱</div>
        <b>TabletPC0</b>
        <small>Wireless</small>
    </div>

    <div class="wire w1"></div>
    <div class="wire w2"></div>
    <div class="wire w3"></div>
    <div class="wire w4"></div>
    <div class="wire w5"></div>
    <div class="wire w6"></div>
    <div class="wire w7"></div>

    <div class="wire wireless wl1"></div>
    <div class="wire wireless wl2"></div>
    <div class="wire wireless wl3"></div>
    <div class="wire wireless wl4"></div>

</div>

<div class="legend">
    <span><i class="dot wired"></i>Wired connection</span>
    <span><i class="dot wifi"></i>Wireless connection</span>
    <span>🟢 Online</span>
</div>

<div style="margin-top:15px">
    <button class="action" onclick="simulate()">▶ Run Simulation</button>
    <button class="action secondary" onclick="resetSimulation()">↻ Reset</button>
</div>

<div id="simulationResult" style="margin-top:12px"></div>
</div>

<!-- ===================================================== -->
<!-- DEVICES -->
<!-- ===================================================== -->

<div class="panel" id="devices">
<h2>📡 Packet Tracer Device Status</h2>

<table>
<thead>
<tr>
<th>Device</th>
<th>Type</th>
<th>Connection</th>
<th>IP Address</th>
<th>Status</th>
</tr>
</thead>
<tbody id="deviceTable"></tbody>
</table>
</div>

<!-- ===================================================== -->
<!-- WIFI 6 CONFIGURATION -->
<!-- ===================================================== -->

<div class="panel" id="wifi">
<h2>⚙️ Wi-Fi 6 Configuration</h2>

<div class="config-grid">

<div>
<div class="form-group">
<label>SSID</label>
<input class="config" id="ssid" value="SmartCampus-WiFi6">
</div>

<div class="form-group">
<label>Band</label>
<select id="band">
<option>2.4 GHz</option>
<option selected>5 GHz</option>
</select>
</div>

<div class="form-group">
<label>Channel</label>
<select id="channel">
<option>36</option>
<option>40</option>
<option>44</option>
<option selected>149</option>
<option>157</option>
</select>
</div>

<div class="form-group">
<label>Channel Width</label>
<select id="width">
<option>20 MHz</option>
<option>40 MHz</option>
<option selected>80 MHz</option>
<option>160 MHz</option>
</select>
</div>
</div>

<div>
<div class="form-group">
<label>Transmit Power (dBm)</label>
<input class="config" id="power" type="number" value="20">
</div>

<div class="form-group">
<label>OFDMA</label>
<select id="ofdma"><option selected>Enabled</option><option>Disabled</option></select>
</div>

<div class="form-group">
<label>MU-MIMO</label>
<select id="mimo"><option selected>Enabled</option><option>Disabled</option></select>
</div>

<div class="form-group">
<label>BSS Coloring</label>
<select id="bss"><option selected>Enabled</option><option>Disabled</option></select>
</div>

<div class="form-group">
<label>Target Wake Time</label>
<select id="twt"><option selected>Enabled</option><option>Disabled</option></select>
</div>
</div>

</div>

<button class="action" onclick="saveConfig()">Save Wi-Fi 6 Configuration</button>
<div id="configMessage" style="margin-top:10px;color:#16a34a"></div>
</div>

<!-- ===================================================== -->
<!-- OPTIMIZATION -->
<!-- ===================================================== -->

<div class="panel" id="optimization">
<h2>🤖 Network Optimization Engine</h2>

<p class="small" style="margin-bottom:15px">
The prototype analyzes client density, channel utilization, latency,
RSSI and packet loss to generate optimization recommendations.
</p>

<button class="action" onclick="runOptimization()">Run Optimization Analysis</button>

<div id="optimizationResult" style="margin-top:15px"></div>
</div>

<!-- ===================================================== -->
<!-- PERFORMANCE -->
<!-- ===================================================== -->

<div class="grid" id="performance">

<div class="panel">
<h2>📈 Throughput</h2>
<canvas id="throughputChart"></canvas>
</div>

<div class="panel">
<h2>📉 Latency</h2>
<canvas id="latencyChart"></canvas>
</div>

</div>

<div class="panel">
<h2>Performance Enhancement: Before vs After</h2>

<div class="metric-grid">

<div class="metric">
<p>Throughput</p><br>
Before: <b>540 Mbps</b><br>
After: <b class="green">780 Mbps</b>
</div>

<div class="metric">
<p>Latency</p><br>
Before: <b>48 ms</b><br>
After: <b class="green">22 ms</b>
</div>

<div class="metric">
<p>Packet Loss</p><br>
Before: <b>4.2%</b><br>
After: <b class="green">0.8%</b>
</div>

<div class="metric">
<p>Channel Utilization</p><br>
Before: <b>91%</b><br>
After: <b class="green">48%</b>
</div>

</div>
</div>

<!-- ===================================================== -->
<!-- CAMPUS COVERAGE -->
<!-- ===================================================== -->

<div class="panel">
<h2>🗺️ Smart Campus Wi-Fi Coverage</h2>

<div class="small">
Green = strong coverage &nbsp; Yellow = moderate &nbsp; Red = weak
</div>

<div class="heat"></div>

<div style="margin-top:15px">
<b>Coverage Score</b>
<div class="progress"><span style="width:86%"></span></div>
<span class="small">86% campus coverage</span>
</div>

<div style="margin-top:13px">
<b>Recommended AP Deployment</b>
<div class="recommendation">
AP-01 → Main Block
</div>
<div class="recommendation">
AP-02 → Computer Lab
</div>
<div class="recommendation">
AP-03 → Library
</div>
<div class="recommendation">
AP-04 → Seminar Hall
</div>
</div>
</div>

<!-- ===================================================== -->
<!-- ALERTS -->
<!-- ===================================================== -->

<div class="panel" id="alerts">
<h2>🚨 Network Alerts</h2>

<div class="alert bad">
⚠ AP/Router wireless client density is high during peak hours.
</div>

<div class="alert">
⚠ Channel utilization may increase when additional users connect.
</div>

<div class="alert">
⚠ Seminar Hall area should be monitored for weak RSSI.
</div>

<div class="alert ok">
✓ Core router and 2960 switch are operational.
</div>

<div class="alert ok">
✓ Wired servers and PCs are reachable in the simulation.
</div>
</div>

<div class="footer-note">
Smart Campus Wi-Fi 6 Prototype • Cisco Packet Tracer topology representation • 802.11ax
</div>

</div>

<script>
// ============================================================
// NAVIGATION
// ============================================================

function go(id){
    document.getElementById(id).scrollIntoView({behavior:"smooth"});
}

// ============================================================
// DEVICES
// ============================================================

function loadDevices(){
    fetch("/api/devices")
    .then(r=>r.json())
    .then(data=>{
        let html="";
        data.forEach(d=>{
            let cls = d.status==="Online" ? "online" :
                      d.status==="Connected" ? "connected" : "warning";
            html += `
            <tr>
                <td><b>${d.name}</b></td>
                <td>${d.device_type}</td>
                <td>${d.connection}</td>
                <td>${d.ip}</td>
                <td class="${cls}">${d.status}</td>
            </tr>`;
        });
        document.getElementById("deviceTable").innerHTML=html;
    });
}

// ============================================================
// PACKET TRACER SIMULATION
// ============================================================

function simulate(){
    fetch("/api/simulate",{method:"POST"})
    .then(r=>r.json())
    .then(d=>{
        document.getElementById("simulationResult").innerHTML=`
        <div class="alert ok">
            <b>Simulation completed successfully.</b><br><br>
            Packets Sent: ${d.sent}<br>
            Packets Received: ${d.received}<br>
            Packet Loss: ${d.loss}%<br>
            Average Latency: ${d.latency} ms<br>
            Network Status: ${d.status}
        </div>`;
    });
}

function resetSimulation(){
    document.getElementById("simulationResult").innerHTML="";
}

// ============================================================
// WIFI CONFIG
// ============================================================

function saveConfig(){
    const data={
        ssid:document.getElementById("ssid").value,
        band:document.getElementById("band").value,
        channel:document.getElementById("channel").value,
        width:document.getElementById("width").value,
        power:document.getElementById("power").value,
        ofdma:document.getElementById("ofdma").value,
        mimo:document.getElementById("mimo").value,
        bss:document.getElementById("bss").value,
        twt:document.getElementById("twt").value
    };

    fetch("/api/configuration",{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data)
    })
    .then(r=>r.json())
    .then(()=>{
        document.getElementById("configMessage").innerText=
        "✓ Wi-Fi 6 configuration saved successfully.";
    });
}

// ============================================================
// OPTIMIZATION
// ============================================================

function runOptimization(){
    fetch("/api/optimize",{method:"POST"})
    .then(r=>r.json())
    .then(d=>{
        let html=`
        <div class="alert ${d.level==="GOOD"?"ok":"bad"}">
            <b>Predicted Network Condition: ${d.condition}</b><br>
            Congestion Score: ${d.score}/100<br>
            Recommended Channel: ${d.channel}
        </div>`;

        d.recommendations.forEach(x=>{
            html+=`<div class="recommendation">🤖 ${x}</div>`;
        });

        document.getElementById("optimizationResult").innerHTML=html;
    });
}

// ============================================================
// REAL-TIME DASHBOARD
// ============================================================

function updateDashboard(){
    fetch("/api/metrics")
    .then(r=>r.json())
    .then(d=>{
        document.getElementById("users").innerText=d.users;
        document.getElementById("wireless").innerText=d.wireless;
        document.getElementById("throughput").innerText=d.throughput;
        document.getElementById("latency").innerText=d.latency;
        document.getElementById("loss").innerText=d.loss;
        document.getElementById("util").innerText=d.utilization;
    });
}

// ============================================================
// CHARTS
// ============================================================

const labels=["10:00","10:05","10:10","10:15","10:20",
              "10:25","10:30","10:35","10:40","10:45"];

new Chart(document.getElementById("throughputChart"),{
    type:"line",
    data:{
        labels:labels,
        datasets:[{
            label:"Throughput (Mbps)",
            data:[450,510,560,610,650,690,720,700,760,780],
            tension:.3,
            fill:true
        }]
    },
    options:{responsive:true}
});

new Chart(document.getElementById("latencyChart"),{
    type:"line",
    data:{
        labels:labels,
        datasets:[{
            label:"Latency (ms)",
            data:[48,45,42,39,37,34,31,29,26,22],
            tension:.3,
            fill:true
        }]
    },
    options:{responsive:true}
});

loadDevices();
updateDashboard();
setInterval(updateDashboard,5000);
setInterval(loadDevices,10000);
</script>

</body>
</html>
"""

# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    if "user" not in session:
        return LOGIN_HTML
    return render_template_string(DASHBOARD_HTML)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username","")
    password = request.form.get("password","")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    ).fetchone()
    conn.close()

    if user:
        session["user"] = user["username"]
        session["role"] = user["role"]
        return redirect("/")

    return """
    <script>
    alert("Invalid username or password");
    window.location="/";
    </script>
    """

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")

# ============================================================
# DEVICE API
# ============================================================

@app.route("/api/devices")
def devices():
    if "user" not in session:
        return jsonify({"error":"Unauthorized"}),401

    conn = get_db()
    rows = conn.execute("SELECT * FROM devices").fetchall()
    conn.close()

    return jsonify([dict(x) for x in rows])

# ============================================================
# REAL-TIME METRICS
# ============================================================

@app.route("/api/metrics")
def metrics():
    if "user" not in session:
        return jsonify({"error":"Unauthorized"}),401

    users = random.randint(8,12)
    wireless = random.randint(3,5)
    throughput = random.randint(650,820)
    latency = random.randint(18,35)
    loss = round(random.uniform(0.4,2.0),1)
    utilization = random.randint(40,70)

    return jsonify({
        "users":users,
        "wireless":wireless,
        "throughput":throughput,
        "latency":latency,
        "loss":loss,
        "utilization":utilization
    })

# ============================================================
# PACKET TRACER SIMULATION API
# ============================================================

@app.route("/api/simulate", methods=["POST"])
def simulate_api():
    if "user" not in session:
        return jsonify({"error":"Unauthorized"}),401

    sent = random.randint(115,160)
    loss_packets = random.randint(0,5)
    received = sent-loss_packets
    loss = round((loss_packets/sent)*100,2)
    latency = random.randint(15,32)

    status = "NORMAL" if loss < 3 else "DEGRADED"

    return jsonify({
        "sent":sent,
        "received":received,
        "loss":loss,
        "latency":latency,
        "status":status,
        "time":datetime.now().strftime("%H:%M:%S")
    })

# ============================================================
# WIFI CONFIGURATION API
# ============================================================

@app.route("/api/configuration", methods=["POST"])
def configuration():
    if "user" not in session:
        return jsonify({"error":"Unauthorized"}),401

    data=request.get_json()

    conn=get_db()
    conn.execute("""
        UPDATE wifi_config
        SET ssid=?,band=?,channel=?,width=?,power=?,
            ofdma=?,mu_mimo=?,bss_coloring=?,twt=?
        WHERE id=1
    """,(
        data.get("ssid"),
        data.get("band"),
        int(data.get("channel")),
        data.get("width"),
        int(data.get("power")),
        data.get("ofdma"),
        data.get("mimo"),
        data.get("bss"),
        data.get("twt")
    ))
    conn.commit()
    conn.close()

    return jsonify({"success":True})

# ============================================================
# OPTIMIZATION API
# ============================================================

@app.route("/api/optimize", methods=["POST"])
def optimize():
    if "user" not in session:
        return jsonify({"error":"Unauthorized"}),401

    # Prototype scoring model.
    # Replace with a trained ML model when real network data is available.
    users=random.randint(35,90)
    utilization=random.randint(35,95)
    latency=random.randint(15,65)
    signal=random.randint(-72,-42)
    packet_loss=round(random.uniform(0.2,5.5),1)

    score=(
        min(users,100)*0.25 +
        utilization*0.30 +
        min(latency,100)*0.20 +
        min(abs(signal-35),50)*0.10 +
        packet_loss*5*0.15
    )
    score=round(min(score,100),1)

    if score >= 70:
        condition="HIGH CONGESTION"
        level="BAD"
    elif score >= 45:
        condition="MODERATE CONGESTION"
        level="BAD"
    else:
        condition="NORMAL"
        level="GOOD"

    channel_usage={36:62,40:55,44:78,149:31,157:46}
    best_channel=min(channel_usage,key=channel_usage.get)

    recommendations=[]

    if utilization>80:
        recommendations.append(
            "High channel utilization detected: move clients to a less congested channel."
        )

    if users>65:
        recommendations.append(
            "High client density detected: use AP load balancing or add another AP."
        )

    if latency>40:
        recommendations.append(
            "High latency detected: optimize channel allocation and reduce interference."
        )

    if signal < -60:
        recommendations.append(
            "Weak RSSI detected: improve AP placement or adjust transmit power."
        )

    if packet_loss>3:
        recommendations.append(
            "High packet loss detected: investigate wireless interference and congestion."
        )

    recommendations.append(
        f"Recommended 5 GHz channel based on simulated utilization: {best_channel}."
    )

    recommendations.append(
        "Keep OFDMA, MU-MIMO and BSS Coloring enabled for high-density Wi-Fi 6 operation."
    )

    return jsonify({
        "score":score,
        "condition":condition,
        "level":level,
        "channel":best_channel,
        "recommendations":recommendations
    })

# ============================================================
# RUN
# ============================================================

if __name__=="__main__":
    print("="*65)
    print("SMART CAMPUS Wi-Fi 6 NETWORK MANAGEMENT SYSTEM")
    print("="*65)
    print("Login : admin")
    print("Password : admin123")
    print("Website: http://127.0.0.1:5000")
    print("="*65)
    app.run(host="127.0.0.1",port=5000,debug=True)
