# Testprotokoll: Hybrider PQC Nginx Reverse Proxy
Dieses Dokument protokolliert die Testergebnisse des hybriden Post-Quantum Nginx Reverse Proxy Setups.

**Testumgebung:**
* Nginx-Proxy-Hostname (intern): `nginx-proxy`
  * [ssl-conf](/nginx-pqc/nginx_config/conf/snippets/ssl-params.conf)
  * [pqc-conf](/nginx-pqc/nginx_config/conf/sites-available/pqc-proxy.conf)
  * [nginx-conf](/nginx-pqc/nginx_config/conf/nginx.conf)
* Zertifikat CN / Servername für SNI: `pqc.tls.proxy`
  * klassisch und selbstsigniert
* KEMs
  * Post-Quantum: `X25519MLKEM768`
  * Klassisch: `X25519`
* OpenSSL-Version
  * PQC-Client: `3.5.0`
  * Nginx-Proxy: `3.5.0`
  * Klassischer Client: `3.0.2`

**Forschungsfrage:**
* Inwiefern beeinflusst ein hybrider PQC-Nginx-Reverse-Proxy (PQC-KEM, klassisches Zertifikat) die TLS-Sicherheit und gewährleistet gleichzeitig die Interoperabilität mit nicht-PQC-fähigen Clients sowie die Kompatibilität mit einer klassischen PKI?

**Hypothesen:**
* Die Vertraulichkeit der ausgetauschten Sitzungsschlüssel ist bei PQC-fähigen Clients durch den PQC-KEM auch dann noch gegeben, wenn klassische Algorithmen kompromittiert sind.
* Die Authentizität des Servers, gewährleistet durch das klassische Zertifikat, bleibt von der Einführung des PQC-KEM unberührt und auf dem gleichen Sicherheitsniveau wie bei klassischen TLS-Implementierungen.
* Für nicht-PQC-fähige Clients findet keine wahrnehmbare Veränderung im Verbindungsaufbau oder in der Verbindungsqualität statt.
* Prozesse wie Zertifikatsausstellung, -validierung und -management bleiben für den Serverbetreiber und die Clients unverändert und funktionieren wie bei klassischen TLS-Implementierungen.

---

## Testfall 1: PQC-fähiger Client (`client-pqc`)

**Befehl:**
(Ausgeführt im `client-pqc` Container)
```bash
docker-compose exec client-pqc bash
```

### 1.1 `openssl s_client` Test

#### 1.1.1 Ziel 
Ziel des Tests ist ein Nachweis einer erfolgreichen TLS-Verbindung zwischen einem pq-fähigen Client und Nginx-Reverse-Proxy. Dabei soll ein hybrider Post-Quantum Key Exchange Mechanism (KEM) aus der [ssl-conf](/nginx-pqc/nginx_config/conf/snippets/ssl-params.conf) mit dem Nginx-Reverse-Proxy ausgehandelt und verwendet werden.

#### 1.1.2 Methode
Innerhalb des client-pqc Docker-Containers wurde openssl s_client ausgeführt. Der vollständige Befehl lautete:
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername pqc.tls.proxy
```

#### 1.1.3 Ergebnis

Der TLS-Handshake wurde erfolgreich durchgeführt.
Die [Ausgabe](testergebnisse/s_client-pq-client.txt) von openssl s_client zeigt die folgenden entscheidenden Parameter für die ausgehandelte Verbindung:
```
subject=CN=pqc.tls.proxy, O=PQCTest, C=DE
issuer=CN=pqc.tls.proxy, O=PQCTest, C=DE
---
Peer signing digest: SHA256
Peer signature type: rsa_pss_rsae_sha256
Negotiated TLS1.3 group: X25519MLKEM768     <-- ERFOLG!
---
SSL handshake has read 2499 bytes and written 1495 bytes
Verification error: self-signed certificate
---
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Protocol: TLSv1.3
Server public key is 2048 bit
...
Verify return code: 18 (self-signed certificate)
```

#### 1.1.4 Analyse
Die Zeile Negotiated TLS1.3 group: `X25519MLKEM768` belegt eindeutig, dass der für die Sitzung verwendete Schlüssel sowohl auf dem klassischen Elliptic-Curve-Algorithmus X25519 als auch auf dem Post-Quantum-Algorithmus ML-KEM (Kyber) basiert.

Gleichzeitig wurde die Verbindung über das moderne Protokoll TLSv1.3 mit der starken Cipher Suite `TLS_AES_256_GCM_SHA384` aufgebaut. Die Authentifizierung des Servers erfolgte, wie beabsichtigt, über ein klassisches 2048-Bit-RSA-Zertifikat. 

Der erwartete Verifizierungsfehler (Verify return code: 18) resultiert aus der Verwendung eines selbstsignierten Zertifikats in der Testumgebung und beeinträchtigt nicht die Gültigkeit des Handshake-Tests.

### 1.2 `curl` Test

#### 1.2.1 Ziel
Das Ziel dieses Tests war es, die Ende-zu-Ende-Konnektivität mit einem Standard-HTTP-Client (curl) zu verifizieren. Es sollte nachgewiesen werden, dass der Proxy eine TLS-Verbindung terminieren und Anfragen eines pq-fähigen Clients korrekt zum Backend weiterleiten kann.

#### 1.2.2 Methode
Innerhalb des client-pqc Docker-Containers wurde curl im Verbose-Modus (-v) ausgeführt, Die Option -k wurde verwendet, um die Zertifikatsprüfung aufgrund des selbstsignierten Zertifikats zu deaktivieren. Der Befehl lautete:
```bash
curl -v https://nginx-proxy -k
```

#### 1.2.2 Ergebnis
Der Test war erfolgreich. Die [Ausgabe](testergebnisse/curl-pq-client.txt) von curl zeigt eine erfolgreich aufgebautet TLS-Verbindung und eine HTTP/1.1 200 OK Antwort vom Server. Die gekürzte Ausgabe zeigt die wesentlichen Schritte:
```
* Connected to nginx-proxy (172.19.0.2) port 443 (#0)
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
* Server certificate:
* subject: CN=pqc.tls.proxy; O=PQCTest; C=DE
* SSL certificate verify result: self-signed certificate (18), continuing anyway.
> GET / HTTP/1.1
> Host: nginx-proxy
> User-Agent: curl/7.81.0
> 
< HTTP/1.1 200 OK
< Server: nginx/1.28.0
< Content-Type: application/json
< 
{"server_info":{...},"status":"online",...}
* Connection #0 to host nginx-proxy left intact
```

#### 1.2.3 Analyse
Das Ergebnis demonstriert die funktionale Korrektheit des Reverse-Proxy-Setups. Ein Standard-Client wie curl kann sich erfolgreich über TLS 1.3 verbinden und Daten mit dem Backend austauschen.

Die Verwendung der Option -k war notwendig, da das Test-Setup ein selbstsigniertes Zertifikat nutzt, dessen Aussteller (issuer) dem Client unbekannt ist. Zudem umgeht -k den Hostname-Mismatch-Fehler, der auftritt, weil der Client den Host nginx-proxy anfragt, das Zertifikat aber auf pqc.tls.proxy ausgestellt ist.

Wichtig ist, dass curl selbst nicht direkt anzeigt, welcher Key Exchange Mechanism (KEM) verwendet wurde. Um nachzuweisen, dass bei dieser curl-Anfrage vom PQC-Client tatsächlich der hybride KEM X25519MLKEM768 zum Einsatz kam, muss dieses Ergebnis mit der Analyse der Nginx Access Logs (siehe letzte Zeile aus [Ausgabe](testergebnisse/curl-pq-client.txt)) korreliert werden. Der Logeintrag bestätigt serverseitig, welcher KEM für die Verbindung von der IP-Adresse des client-pqc Containers ausgehandelt wurde.

## Testfall 2: Klassischer Client (`client-classic`)
**Befehl:**
(Ausgeführt im `client-classic` Container)
```bash
docker-compose exec client-classic bash
```

### 2.1 `openssl s_client` Test

#### 2.1.1 Ziel
Ziel des Tests ist ein Nachweis einer erfolgreichen TLS-Verbindung zwischen einem klassischen Client und Nginx-Reverse-Proxy. Dabei soll ein klassisches Key Exchange Mechanism (KEM) aus der [ssl-conf](/nginx-pqc/nginx_config/conf/snippets/ssl-params.conf) mit dem Nginx-Reverse-Proxy ausgehandelt und verwendet werden.

#### 2.1.2 Methode
Innerhalb des client-classic Docker-Containers wurde openssl s_client ausgeführt. Der vollständige Befehl lautete:
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername pqc.tls.proxy
```

#### 2.1.2 Ergebnis
Der TLS-Handshake wurde erfolgreich durchgeführt. Die [Ausgabe](testergebnisse/s_client-classic-client.txt) von openssl s_client zeigt die folgenden entscheidenden Parameter für die ausgehandelte Verbindung:
```
subject=CN = pqc.tls.proxy, O = PQCTest, C = DE
issuer=CN = pqc.tls.proxy, O = PQCTest, C = DE
---
No client certificate CA names sent
Peer signing digest: SHA256
Peer signature type: RSA-PSS
Server Temp Key: X25519, 253 bits        <-- ERFOLG!
---
SSL handshake has read 1421 bytes and written 328 bytes
Verification error: self-signed certificate
---
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Server public key is 2048 bit
...
Verify return code: 18 (self-signed certificate)
```

#### 2.1.3 Analyse
Die Zeile Server Temp Key: X25519, 253 bits ist der entscheidende Nachweis dafür, dass ein rein klassischer Schlüsselaustauschmechanismus (Elliptic-Curve Diffie-Hellman mit der Kurve X25519) ausgehandelt und verwendet wurde.

Gleichzeitig wurde die Verbindung, wie erwartet, über das moderne Protokoll TLS 1.3 mit einer starken Cipher Suite (TLS_AES_256_GCM_SHA384) gesichert. Die Authentifizierung des Servers erfolgte, wie beabsichtigt, über ein klassisches 2048-Bit-RSA-Zertifikat.

Der erwartete Verifizierungsfehler (Verify return code: 18) resultiert aus der Verwendung eines selbstsignierten Zertifikats in der Testumgebung und beeinträchtigt nicht die Gültigkeit des Handshake-Tests.

### 2.2 `curl` Test

#### 2.2.1 Ziel
Das Ziel dieses Tests war es, die Ende-zu-Ende-Konnektivität mit einem Standard-HTTP-Client (curl) zu verifizieren. Es sollte nachgewiesen werden, dass der Proxy eine TLS-Verbindung terminieren und Anfragen eines klassischen Clients korrekt zum Backend weiterleiten kann.

#### 2.2.2 Methode
Innerhalb des client-classic Docker-Containers wurde curl im Verbose-Modus (-v) ausgeführt, Die Option -k wurde verwendet, um die Zertifikatsprüfung aufgrund des selbstsignierten Zertifikats zu deaktivieren. Der Befehl lautete:
```bash
curl -v https://nginx-proxy -k
```

#### 2.2.2 Ergebnis
Der Test war erfolgreich. Die [Ausgabe](testergebnisse/curl-classic-client.txt) von curl zeigt eine erfolgreich aufgebautet TLS-Verbindung und eine HTTP/1.1 200 OK Antwort vom Server. Die gekürzte Ausgabe zeigt die wesentlichen Schritte:
```
* Connected to nginx-proxy (172.20.0.2) port 443 (#0)
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384
* Server certificate:
* subject: CN=pqc.tls.proxy; O=PQCTest; C=DE
* SSL certificate verify result: self-signed certificate (18), continuing anyway.
> GET / HTTP/1.1
> Host: nginx-proxy
> User-Agent: curl/7.81.0
> 
< HTTP/1.1 200 OK
< Server: nginx/1.28.0
< Content-Type: application/json
< 
{"server_info":{"hostname":"cedab2a3948d",...}}
* Connection #0 to host nginx-proxy left intact
```

#### 2.2.3 Analyse
Dieses Ergebnis bestätigt die vollständige funktionale Interoperabilität des Reverse-Proxy-Setups. Ein HTTP-Client ohne PQC-Fähigkeiten kann den gesamten Kommunikationsweg (Client → Proxy → Backend → Client) erfolgreich durchlaufen.

Die Verwendung der Option -k war notwendig, da das Test-Setup ein selbstsigniertes Zertifikat nutzt, dessen Aussteller (issuer) dem Client unbekannt ist. Zudem umgeht -k den Hostname-Mismatch-Fehler, der auftritt, weil der Client den Host nginx-proxy anfragt, das Zertifikat aber auf pqc.tls.proxy ausgestellt ist.

Wichtig ist, dass curl selbst nicht direkt anzeigt, welcher Key Exchange Mechanism (KEM) verwendet wurde. Um nachzuweisen, dass bei dieser curl-Anfrage vom klassischen Client tatsächlich der klassische KEM X25519 zum Einsatz kam, muss dieses Ergebnis mit der Analyse der Nginx Access Logs (siehe letzte Zeile aus [Ausgabe](testergebnisse/curl-classic-client.txt)) korreliert werden. Der Logeintrag bestätigt serverseitig, welcher KEM für die Verbindung von der IP-Adresse des client-pqc Containers ausgehandelt wurde.

## 3. Performance-Analyse des TLS-Handshakes
Um die Performance-Auswirkungen des hybriden PQC-Ansatzes zu quantifizieren, 
wurde die Anzahl der möglichen TLS-Handshakes pro Sekunde gemessen. 
Als Testwerkzeug kam `openssl s_time` mit einer Laufzeit von 60 Sekunden pro Testlauf zum Einsatz.

Es wurden zwei Szenarien verglichen:
1.  **Klassischer Handshake:** Ein Client mit einer Standard-System-OpenSSL-Bibliothek, der einen klassischen KEM (ECDHE mit X25519) aushandelt.
2.  **PQC-Handshake:** Ein Client mit einer neueren, PQC-fähigen OpenSSL-Bibliothek, der den hybriden KEM `X25519MLKEM768` aushandelt, was durch die Server-Logs verifiziert wurde.

### 3.1 Methode
```bash
openssl s_time -connect nginx-proxy:443 -www / -new -time 60
```

### 3.2 Messergebnisse
Die durchgeführten Tests ergaben die folgenden Performance-Werte.

| Metrik                            | Klassischer Handshake (OpenSSL 3.0.2) | Hybrider PQC-Handshake (OpenSSL 3.5.0)       | Veränderung |
|:----------------------------------|:--------------------------------------|:---------------------------------------------|:------------|
| **Gesamte Verbindungen (60s)**    | 19,117                                | **20,454**                                   | **+7.0 %**  |
| **Verbindungen/Sekunde (Real)**   | **~313**                              | **~335**                                     | **+7.0 %**  |
| **Durchschnittl. Handshake-Zeit** | ~3.19 ms                              | **~2.98 ms**                                 | **-6.6 %**  |
| **CPU-Zeit pro Handshake**        | ~0.58 ms                              | **~0.43 ms**                                 | **-25.9 %** |

*Tabelle 3.2: Performance-Vergleich von klassischem und 
hybridem PQC-TLS-Handshake über unterschiedliche OpenSSL-Versionen.*

### 3.3 Analyse und Diskussion
Die Messergebnisse in Tabelle 5.1 zeigen das auf den ersten Blick unerwartete Resultat, 
dass der TLS-Handshake mit dem hybriden PQC-Algorithmus `X25519MLKEM768` 
eine um etwa 7 % höhere Performance aufweist als der rein klassische Handshake.

Diese Leistungssteigerung ist jedoch nicht auf den PQC-Algorithmus selbst zurückzuführen. 
Vielmehr verdeutlicht das Ergebnis den signifikanten Einfluss der zugrundeliegenden 
Kryptographie-Bibliothek. Der PQC-Test wurde mit einer neueren, 
für moderne CPUs optimierten OpenSSL-Version durchgeführt, 
während der klassische Test auf einer älteren System-Bibliothek lief. 
Die allgemeinen Optimierungen in der neueren OpenSSL-Version sind so effektiv, 
dass sie den zusätzlichen Rechenaufwand des Post-Quantum-Algorithmus kompensieren und 
im Vergleich zur älteren Bibliothek sogar zu einer besseren Gesamtperformance führen.

**Fazit:** Der Einsatz von PQC muss nicht zwangsläufig zu einem Performance-Verlust führen, 
wenn er im Rahmen einer Aktualisierung auf eine moderne, hoch-optimierte Krypto-Bibliothek 
erfolgt. Die Wahl einer aktuellen Software-Basis kann den potenziellen 
PQC-Overhead minimieren oder, wie in diesem Test gezeigt, sogar überkompensieren.

## 4. Performance-Analyse: PQC-Overhead

Um den reinen Performance-Overhead des Post-Quantum-Algorithmus zu isolieren, 
wurde ein direkter Vergleich auf Basis derselben Krypto-Bibliothek (OpenSSL 3.5.0) durchgeführt. 
Dabei wurde im `client-pqc` Container einmal ein klassischer Handshake (ECDHE mit X25519) und 
einmal ein hybrider PQC-Handshake (X25519MLKEM768) erzwungen. 
Die Tests liefen jeweils über eine Dauer von 60 Sekunden.

### 4.1 Messergebnisse des isolierten Vergleichs

| Metrik                            | Klassischer Handshake (X25519 auf neuer Lib) | Hybrider PQC-Handshake (X25519MLKEM768) | Veränderung (PQC-Overhead) |
|:----------------------------------|:---------------------------------------------|:----------------------------------------|:---------------------------|
| **Gesamte Verbindungen (60s)**    | 20,300                                       | 18,058                                  | -11.0 %                    |
| **Verbindungen/Sekunde (Real)**   | **~333**                                     | **~296**                                | **-11.1 %**                |
| **Durchschnittl. Handshake-Zeit** | ~3.00 ms                                     | ~3.38 ms                                | +12.7 %                    |
| **CPU-Zeit pro Handshake**        | ~0.42 ms                                     | ~0.50 ms                                | +19.0 %                    |

*Tabelle 5.1: Direkter Performance-Vergleich zur Ermittlung des PQC-Overheads.*

### 4.2 Analyse und Diskussion

Der direkte Vergleich unter Verwendung derselben optimierten 
OpenSSL-Bibliothek ermöglicht eine präzise Quantifizierung 
des durch den PQC-Algorithmus verursachten Overheads.

Der Test des klassischen Handshakes mit X25519 erreichte 
**ca. 333 Verbindungen pro Sekunde** und dient als präzise Baseline. 
Im Vergleich dazu erreichte der hybride Handshake mit X25519MLKEM768 
**ca. 296 Verbindungen pro Sekunde**. Dies entspricht einer 
**Performance-Reduzierung von ca. 11,1 %**.

Dieser messbare Overhead ist direkt auf die zusätzlichen 
kryptographischen Berechnungen des ML-KEM-Algorithmus zurückzuführen. 
Die reine CPU-Zeit pro Handshake erhöhte sich um ca. 19 %, was den 
höheren Rechenaufwand verdeutlicht. Dieser "Preis" für die quantenresistente 
Absicherung der Vertraulichkeit gegen zukünftige "Harvest Now, 
Decrypt Later"-Angriffe ist ein entscheidender Faktor bei der Planung von Migrationen.

Ein Overhead von ca. 11 % im Verbindungsaufbau kann für die meisten Webanwendungen 
als akzeptabel angesehen werden, insbesondere da er nur den einmaligen Handshake 
betrifft und nicht den Datendurchsatz bestehender Verbindungen. Die Ergebnisse zeigen, 
dass eine Migration zu hybrider Post-Quantum-Kryptographie mit einem überschaubaren 
und klar messbaren Performance-Aufwand möglich ist.

### Für eine noch tiefere akademische Analyse (Optional)
Um den **reinen Overhead des PQC-Algorithmus** zu isolieren,
könnten Sie einen dritten Testlauf durchführen:

* **Verwenden Sie den `client-pqc` Container** (mit der neuen OpenSSL-Version).
* **Erzwingen Sie dort aber einen rein klassischen Handshake** (z.B. mit einer Konfigurationsdatei, die `Groups = X25519` setzt).

Wenn Sie dann das Ergebnis von `(PQC auf neuer Lib)` mit `(Klassisch auf neuer Lib)` vergleichen,
sehen Sie den wahren Performance-Unterschied der Algorithmen selbst,
ohne den Einfluss der unterschiedlichen Bibliotheksversionen.
Das wäre eine exzellente Ergänzung für Ihre Arbeit.

