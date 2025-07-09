# Testprotokoll: Hybrider PQC Nginx Reverse Proxy
Dieses Dokument protokolliert die Testergebnisse des hybriden Post-Quantum Nginx Reverse Proxy Setups.

**Testumgebung:**
* Nginx-Proxy: `nginx-proxy`
  * [pqc-conf](/nginx-pqc/nginx_config/conf/sites-available/pqc-proxy.conf)
  * [nginx-conf](/nginx-pqc/nginx_config/conf/nginx.conf)
* Zertifikat CN / Servername für SNI: `pqc.tls.proxy`
  * [Zertifikat](/nginx-pqc/nginx_config/ssl) klassisch und selbst signiert
* KEMs - [ssl-conf](/nginx-pqc/nginx_config/conf/snippets/ssl-params.conf)
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

## `openssl s_client` Tests
**Ziel:**
Ziel dieses Tests ist der Nachweis einer erfolgreichen TLS-Verbindung mit dem Nginx-Reverse-Proxy. Dabei sollen zwei Tests durchgeführt werden, um die jeweiligen Szenarien abzudecken:
* Der PQC-fähiger Client soll mit dem Nginx-Reverse-Proxy einen hybriden Post-Quantum Key Exchange Mechanism (KEM) aushandeln und verwenden.
* Der klassischer Client soll mit dem Nginx-Reverse-Proxy einen klassischen Key Exchange Mechanism (KEM) aushandeln und verwenden.

### 1. PQC-fähiger Client (`client-pqc`)

#### 1.1 Methode
Innerhalb des client-pqc Docker-Containers wurde openssl s_client ausgeführt. Der vollständige Befehl lautete:
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername pqc.tls.proxy
```

#### 1.2 Ergebnis

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

#### 1.3 Analyse
Die Zeile Negotiated TLS1.3 group: `X25519MLKEM768` belegt eindeutig, dass der für die Sitzung verwendete Schlüssel sowohl auf dem klassischen Elliptic-Curve-Algorithmus X25519 als auch auf dem Post-Quantum-Algorithmus ML-KEM (Kyber) basiert.

Gleichzeitig wurde die Verbindung über das moderne Protokoll TLSv1.3 mit der starken Cipher Suite `TLS_AES_256_GCM_SHA384` aufgebaut. Die Authentifizierung des Servers erfolgte, wie beabsichtigt, über ein klassisches 2048-Bit-RSA-Zertifikat.

Der erwartete Verifizierungsfehler (Verify return code: 18) resultiert aus der Verwendung eines selbst signierten Zertifikats in der Testumgebung und beeinträchtigt nicht die Gültigkeit des Handshake-Tests.

### 2. Klassischer Client (`client-classic`)

#### 2.1 Methode
Innerhalb des client-classic Docker-Containers wurde openssl s_client ausgeführt. Der vollständige Befehl lautete:
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername pqc.tls.proxy
```

#### 2.2 Ergebnis
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

#### 2.3 Analyse
Die Zeile Server Temp Key: X25519, 253 bits ist der entscheidende Nachweis dafür, dass ein rein klassischer Schlüsselaustauschmechanismus (Elliptic-Curve Diffie-Hellman mit der Kurve X25519) ausgehandelt und verwendet wurde.

Gleichzeitig wurde die Verbindung, wie erwartet, über das moderne Protokoll TLS 1.3 mit einer starken Cipher Suite (TLS_AES_256_GCM_SHA384) gesichert. Die Authentifizierung des Servers erfolgte, wie beabsichtigt, über ein klassisches 2048-Bit-RSA-Zertifikat.

Der erwartete Verifizierungsfehler (Verify return code: 18) resultiert aus der Verwendung eines selbst signierten Zertifikats in der Testumgebung und beeinträchtigt nicht die Gültigkeit des Handshake-Tests.

---

## `curl` Tests
**Ziel:**
Ziel dieses Tests ist es, die Ende-zu-Ende-Konnektivität mit einem Standard-HTTP-Client (curl) zu verifizieren. Es sollte nachgewiesen werden, dass der Nginx-Reverse-Proxy in der Lage ist, TLS-Verbindungen zu terminieren und Anfragen sowohl von einem PQC-fähigen als auch von einem klassischen Client korrekt an das Backend weiterzuleiten.

### 1. PQC-fähiger Client (`client-pqc`)

#### 1.1 Methode
Innerhalb des client-pqc Docker-Containers wurde curl im Verbose-Modus (-v) ausgeführt, Die Option -k wurde verwendet, um die Zertifikatsprüfung aufgrund des selbst signierten Zertifikats zu deaktivieren. Der Befehl lautete:
```bash
curl -v https://nginx-proxy -k
```

#### 1.2 Ergebnis
Der Test war erfolgreich. Die [Ausgabe](testergebnisse/curl-pq-client.txt) von curl zeigt eine erfolgreich aufgebaute TLS-Verbindung und eine HTTP/1.1 200 OK Antwort vom Server. Die gekürzte Ausgabe zeigt die wesentlichen Schritte:
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

#### 1.3 Analyse
Das Ergebnis demonstriert die funktionale Korrektheit des Reverse-Proxy-Setups. Ein Standard-Client wie curl kann sich erfolgreich über TLS 1.3 verbinden und Daten mit dem Backend austauschen.

Die Verwendung der Option -k war notwendig, da das Test-Setup ein selbst signiertes Zertifikat nutzt, dessen Aussteller (issuer) dem Client unbekannt ist. Zudem umgeht -k den Hostname-Mismatch-Fehler, der auftritt, weil der Client den Host nginx-proxy anfragt, das Zertifikat aber auf pqc.tls.proxy ausgestellt ist.

Wichtig ist, dass curl selbst nicht direkt anzeigt, welcher Key Exchange Mechanism (KEM) verwendet wurde. Um nachzuweisen, dass bei dieser curl-Anfrage vom PQC-Client tatsächlich der hybride KEM X25519MLKEM768 zum Einsatz kam, muss dieses Ergebnis mit der Analyse der Nginx Access Logs (siehe letzte Zeile aus [Ausgabe](testergebnisse/curl-pq-client.txt)) korreliert werden. Der Logeintrag bestätigt serverseitig, welcher KEM für die Verbindung von der IP-Adresse des client-pqc Containers ausgehandelt wurde.

### 2. Klassischer Client (`client-classic`)

#### 2.1 Methode
Innerhalb des client-classic Docker-Containers wurde curl im Verbose-Modus (-v) ausgeführt, Die Option -k wurde verwendet, um die Zertifikatsprüfung aufgrund des selbst signierten Zertifikats zu deaktivieren. Der Befehl lautete:
```bash
curl -v https://nginx-proxy -k
```

#### 2.2 Ergebnis
Der Test war erfolgreich. Die [Ausgabe](testergebnisse/curl-classic-client.txt) von curl zeigt eine erfolgreich aufgebaute TLS-Verbindung und eine HTTP/1.1 200 OK Antwort vom Server. Die gekürzte Ausgabe zeigt die wesentlichen Schritte:
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

#### 2.3 Analyse
Dieses Ergebnis bestätigt die vollständige funktionale Interoperabilität des Reverse-Proxy-Setups. Ein HTTP-Client ohne PQC-Fähigkeiten kann den gesamten Kommunikationsweg (Client → Proxy → Backend → Client) erfolgreich durchlaufen.

Die Verwendung der Option -k war notwendig, da das Test-Setup ein selbst signiertes Zertifikat nutzt, dessen Aussteller (issuer) dem Client unbekannt ist. Zudem umgeht -k den Hostname-Mismatch-Fehler, der auftritt, weil der Client den Host nginx-proxy anfragt, das Zertifikat aber auf pqc.tls.proxy ausgestellt ist.

Wichtig ist, dass curl selbst nicht direkt anzeigt, welcher Key Exchange Mechanism (KEM) verwendet wurde. Um nachzuweisen, dass bei dieser curl-Anfrage vom klassischen Client tatsächlich der klassische KEM X25519 zum Einsatz kam, muss dieses Ergebnis mit der Analyse der Nginx Access Logs (siehe letzte Zeile aus [Ausgabe](testergebnisse/curl-classic-client.txt)) korreliert werden. Der Logeintrag bestätigt serverseitig, welcher KEM für die Verbindung von der IP-Adresse des client-pqc Containers ausgehandelt wurde.

---

## Performance Tests

### 3 Performance-Analyse des TLS-Handshakes
Um die Performance-Auswirkungen des hybriden PQC-Ansatzes zu quantifizieren, wurde die Anzahl der möglichen TLS-Handshakes pro Sekunde gemessen.

Es wurden zwei Szenarien verglichen:
1. **Klassischer Handshake:** Ein Client mit OpenSSL (3.0.2) der den klassischen KEM `X25519` aushandelt.
2. **PQC-Handshake:** Ein Client mit OpenSSL (3.5.0), der den hybriden KEM `X25519MLKEM768` aushandelt.

#### 3.1 Methode
Als Testwerkzeug kam `openssl s_time` mit einer Laufzeit von 60 Sekunden pro Testlauf zum Einsatz. Der Befehl lautete:
```bash
openssl s_time -connect nginx-proxy:443 -www / -new -time 60
```

#### 3.2 Messergebnisse
Die durchgeführten Tests ergaben die folgenden Performance-Werte.

| Metrik                          | Klassischer Handshake (OpenSSL 3.0.2) | Hybrider PQC-Handshake (OpenSSL 3.5.0) | Veränderung |
|:--------------------------------|:--------------------------------------|:---------------------------------------|:------------|
| **Gesamte Verbindungen (60s)**  | 19,117                                | 20,454                                 | +7.0 %      |
| **Verbindungen/Sekunde (Real)** | ~313                                  | ~335                                   | +7.0 %      |
| **Durchschn. Handshake-Zeit**   | ~3.19 ms                              | ~2.98 ms                               | -6.6 %      |
| **CPU-Zeit pro Handshake**      | ~0.58 ms                              | ~0.43 ms                               | -25.9 %     |

*Tabelle 3.2: Performance-Vergleich von klassischem und
hybridem PQC-TLS-Handshake über unterschiedliche OpenSSL-Versionen.*

#### 3.3 Analyse und Diskussion
Die Messergebnisse in Tabelle 5.1 zeigen das auf den ersten Blick unerwartete Resultat, dass der TLS-Handshake mit dem hybriden PQC-Algorithmus `X25519MLKEM768` eine um etwa 7 % höhere Performance aufweist als der rein klassische Handshake.

Diese Leistungssteigerung ist jedoch nicht auf den PQC-Algorithmus selbst zurückzuführen. Vielmehr verdeutlicht das Ergebnis den signifikanten Einfluss der zugrundeliegenden Kryptografie-Bibliothek und unterschiedlichen Version von OpenSSL. Der PQC-Test wurde mit der neuesten OpenSSL-Version (3.5.0, Stand April 2025) durchgeführt, während der klassische Test auf einer älteren Version (3.0.2) lief. Die allgemeinen Optimierungen in der neueren OpenSSL-Version sind so effektiv, dass sie den zusätzlichen Rechenaufwand des Post-Quantum-Algorithmus kompensieren und im Vergleich sogar zu einer besseren Gesamtperformance führen.

**Fazit:** Der Einsatz von PQC muss nicht zwangsläufig zu einem Performance-Verlust führen, wenn er im Rahmen einer Aktualisierung auf eine moderne, hoch-optimierte Krypto-Bibliothek erfolgt.

---

### 4. Performance-Analyse: PQC-Overhead

Um den reinen Performance-Overhead des Post-Quantum-Algorithmus zu isolieren, wurde ein direkter Vergleich auf Basis derselben Krypto-Bibliothek (OpenSSL 3.5.0) durchgeführt. Dabei wurde im `client-pqc` Container einmal ein klassischer Handshake (ECDHE mit X25519) und einmal ein hybrider PQC-Handshake (X25519MLKEM768) erzwungen.

#### 4.1 Methode
Als Testwerkzeug kam ebenfalls `openssl s_time` mit einer Laufzeit von 60 Sekunden pro Testlauf zum Einsatz. Der Befehl lautete:
```bash
openssl s_time -connect nginx-proxy:443 -www / -new -time 60
```

#### 4.2 Messergebnisse des isolierten Vergleichs

| Metrik                          | Klassischer Handshake (X25519 auf neuer Lib) | Hybrider PQC-Handshake (X25519MLKEM768) | Veränderung (PQC-Overhead) |
|:--------------------------------|:---------------------------------------------|:----------------------------------------|:---------------------------|
| **Gesamte Verbindungen (60s)**  | 20,300                                       | 18,058                                  | -11.0 %                    |
| **Verbindungen/Sekunde (Real)** | ~333                                         | ~296                                    | -11.1 %                    |
| **Durchschn. Handshake-Zeit**   | ~3.00 ms                                     | ~3.38 ms                                | +12.7 %                    |
| **CPU-Zeit pro Handshake**      | ~0.42 ms                                     | ~0.50 ms                                | +19.0 %                    |

*Tabelle 4.2: Direkter Performance-Vergleich zur Ermittlung des PQC-Overheads.*

#### 4.3 Analyse und Diskussion

Der Test des klassischen Handshakes mit `X25519` erreichte **ca. 333 Verbindungen pro Sekunde** und dient als präzise Baseline. Im Vergleich dazu erreichte der hybride Handshake mit `X25519MLKEM768` **ca. 296 Verbindungen pro Sekunde**. Dies entspricht einer **Performance-Reduzierung von ca. 11,1 %**.

Dieser messbare Overhead ist direkt auf die zusätzlichen kryptografischen Berechnungen des ML-KEM-Algorithmus zurückzuführen. Die reine CPU-Zeit pro Handshake erhöhte sich um ca. 19 %, was den höheren Rechenaufwand verdeutlicht. Dieser "Preis" für die quanten resistente Absicherung der Vertraulichkeit gegen zukünftige "Harvest Now, Decrypt Later"-Angriffe ist ein entscheidender Faktor bei der Planung von Migrationen.

Ein Overhead von ca. 11 % im Verbindungsaufbau kann für die meisten Webanwendungen als akzeptabel angesehen werden, insbesondere da er nur den einmaligen Handshake betrifft und nicht den Datendurchsatz bestehender Verbindungen. Die Ergebnisse zeigen, dass eine Migration zu hybrider PQC mit einem überschaubaren und klar messbaren Performance-Aufwand möglich ist.
