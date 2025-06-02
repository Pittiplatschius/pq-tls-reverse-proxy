# Testprotokoll: Hybrider PQC Nginx Reverse Proxy
Dieses Dokument protokolliert die Testergebnisse des hybriden Post-Quantum Nginx Reverse Proxy Setups.

**Datum des Tests:** 27.05.2025

**Testumgebung:**
* Nginx-Proxy-Hostname (intern): `nginx-proxy`
* Zertifikat CN / Servername für SNI: `pqc.tls.proxy`
* KEMs
  * Post-Quantum: `X25519MLKEM768`
  * Klassisch: `X25519`
* OpenSSL-Version
  * PQC-Client: `3.5.0`
  * Klassischer Client: `3.0.2 - System-Version`

---

## Testfall 1: PQC-fähiger Client (`client-pqc`)
Ziel: Überprüfung, ob der PQC-fähige Client eine TLS-Verbindung mit einem 
Post-Quantum Key Exchange Mechanism (KEM) aushandelt.

**Kommandos:**
(Ausgeführt im `client-pqc` Container)
```bash
docker-compose exec client-pqc bash
```

### 1.1 `openssl s_client` Test

#### 1.1.1 Ziel 
Das Ziel dieses Tests war es, nachzuweisen, dass ein PQC-fähiger Client erfolgreich 
eine TLS-Verbindung mit dem Nginx-Reverse-Proxy aushandeln kann, 
bei der ein hybrider Post-Quantum Key Exchange Mechanism (KEM) verwendet wird.

#### 1.1.2 Methode
Innerhalb des client-pqc Docker-Containers wurde openssl s_client 
mit der expliziten Anforderung der hybriden Gruppe X25519MLKEM768 ausgeführt. 
Der vollständige Befehl lautete:
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername pqc.tls.proxy
```

#### 1.1.3 Ergebnis
Der TLS-Handshake wurde erfolgreich abgeschlossen.
Die Analyse der [Ausgabe](testergebnisse/s_client-pq-client.txt) von openssl s_client zeigte 
die folgenden entscheidenden Parameter für die ausgehandelte Verbindung:
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
Das Ergebnis bestätigt den Erfolg des hybriden Ansatzes. 
Die Zeile Negotiated TLS1.3 group: X25519MLKEM768 belegt eindeutig, 
dass der für die Sitzung verwendete Schlüssel sowohl auf dem klassischen 
Elliptic-Curve-Algorithmus X25519 
als auch auf dem Post-Quantum-Algorithmus ML-KEM (Kyber) basiert.

Gleichzeitig wurde die Verbindung über das moderne Protokoll TLSv1.3 
mit der starken Cipher Suite TLS_AES_256_GCM_SHA384 aufgebaut. 
Die Authentifizierung des Servers erfolgte, wie beabsichtigt, 
über ein klassisches 2048-Bit-RSA-Zertifikat. 

Der erwartete Verifizierungsfehler (Verify return code: 18) resultiert 
aus der Verwendung eines selbstsignierten Zertifikats in der Testumgebung 
und beeinträchtigt nicht die Gültigkeit des Handshake-Tests.

### 1.2 `curl` Test

#### 1.2.1 Ziel
Das Ziel dieses Tests war es, die Ende-zu-Ende-Konnektivität 
mit einem Standard-HTTP-Client (curl) zu verifizieren. 
Es sollte nachgewiesen werden, dass der Proxy eine TLS-Verbindung terminieren 
und Anfragen korrekt zum Backend weiterleiten kann.

#### 1.2.2 Methode
Innerhalb des client-pqc Containers wurde curl im Verbose-Modus (-v) ausgeführt. 
Die Option -k wurde verwendet, um die Verifizierung des selbstsignierten Serverzertifikats 
zu umgehen. Der Befehl lautete:
```bash
curl -v https://nginx-proxy -k
```

#### 1.2.2 Ergebnis
Der Test war erfolgreich. curl konnte eine TLS-Verbindung aufbauen und erhielt 
eine HTTP/1.1 200 OK Antwort vom Server. [Vollständige Ausgabe](testergebnisse/curl-pq-client.txt)
Die gekürzte Ausgabe zeigt die wesentlichen Schritte:
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
Das Ergebnis demonstriert die funktionale Korrektheit des Reverse-Proxy-Setups. 
Ein Standard-Client wie curl kann sich erfolgreich über TLS 1.3 verbinden und 
Daten mit dem Backend austauschen.

Die Verwendung der Option -k war notwendig, da das Test-Setup ein selbstsigniertes Zertifikat 
nutzt, dessen Aussteller (issuer) dem Client unbekannt ist. Zudem umgeht -k 
den Hostname-Mismatch-Fehler, der auftritt, weil der Client den Host nginx-proxy anfragt, 
das Zertifikat aber auf pqc.tls.proxy ausgestellt ist.

Wichtig ist, dass curl selbst nicht direkt anzeigt, welcher Key Exchange Mechanism (KEM) 
verwendet wurde. Um nachzuweisen, dass bei dieser curl-Anfrage vom PQC-Client tatsächlich 
der hybride KEM X25519MLKEM768 zum Einsatz kam, muss dieses Ergebnis mit der Analyse 
der Nginx Access Logs (siehe vorherige Tests) korreliert werden. 
Die Logs bestätigen serverseitig, welcher KEM für die Verbindung von der IP-Adresse 
des client-pqc Containers ausgehandelt wurde.

## Testfall 2: Klassischer Client (`client-classic`)
Ziel: Überprüfung, ob der klassische Client eine TLS-Verbindung ohne 
Post-Quantum Key Exchange Mechanism (KEM) aushandelt.

**Kommandos:**
(Ausgeführt im `client-classic` Container)
```bash
docker-compose exec client-classic bash
```

### 2.1 `openssl s_client` Test

#### 2.1.1 Ziel
Das Ziel dieses Tests war es, die Interoperabilität 
des Nginx-Reverse-Proxys mit Clients nachzuweisen, 
die keine Post-Quantum-Algorithmen unterstützen. 
Es sollte verifiziert werden, dass ein solcher Client 
eine sichere Verbindung über einen standardmäßigen, 
klassischen TLS-Handshake erfolgreich aufbauen kann.

#### 2.1.2 Methode
Innerhalb des client-classic Docker-Containers wurde openssl s_client ausgeführt, 
um eine TLS-Verbindung zum Nginx-Proxy zu initiieren. 
Es wurden dabei keine spezifischen Post-Quantum-Gruppen angefordert.
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername proxy.pqc.test
```

#### 2.1.2 Ergebnis
Der Verbindungsaufbau war erfolgreich. Der folgende Auszug aus 
der Terminal-Ausgabe zeigt die entscheidenden Parameter des ausgehandelten Handshakes:
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
Das Ergebnis bestätigt die erfolgreiche Interoperabilität des Servers. 
Die Zeile Server Temp Key: X25519, 253 bits ist der entscheidende Nachweis dafür, 
dass ein rein klassischer Schlüsselaustauschmechanismus 
(Elliptic-Curve Diffie-Hellman mit der Kurve X25519) verwendet wurde.

Dies demonstriert, dass der Nginx-Proxy korrekt auf einen 
klassischen Algorithmus zurückfällt, wenn der Client keine PQC-Verfahren in seinem 
ClientHello anbietet. Die Abwärtskompatibilität ist somit gewährleistet. 
Die Verbindung wurde zudem, wie erwartet, über das moderne Protokoll TLS 1.3 
mit einer starken Cipher Suite (TLS_AES_256_GCM_SHA384) gesichert. 
Der protokollierte Verifizierungsfehler (Verify return code: 18) ist auf das im 
Test-Setup verwendete selbstsignierte Zertifikat zurückzuführen und hat keinen 
Einfluss auf die Gültigkeit des Handshake-Ergebnisses.

### 2.2 `curl` Test

#### 2.2.1 Ziel
Das Ziel dieses Tests war es, die vollständige Ende-zu-Ende-Konnektivität auf 
Anwendungsebene für einen nicht-PQC-fähigen Client zu verifizieren. 
Es sollte gezeigt werden, dass ein Standard-HTTP-Tool (curl) eine Anfrage über 
den Proxy senden und eine gültige Antwort vom Backend-Server empfangen kann.

#### 2.2.2 Methode
Innerhalb des client-classic Docker-Containers wurde curl im Verbose-Modus (-v) ausgeführt, 
um eine HTTPS-GET-Anfrage zu senden. Die Option -k wurde verwendet, 
um die Zertifikatsprüfung aufgrund des selbstsignierten Zertifikats und 
des Hostname-Mismatches zu deaktivieren.
```bash
curl -v https://nginx-proxy -k
```

#### 2.2.2 Ergebnis
Der Test war erfolgreich. curl konnte eine TLS 1.3 Verbindung aufbauen, 
die Anfrage senden und eine HTTP/1.1 200 OK Antwort mit dem JSON-Payload 
vom Backend empfangen. Die gekürzte Ausgabe zeigt die wesentlichen Schritte:
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
Dieses Ergebnis bestätigt die vollständige funktionale Interoperabilität 
des Reverse-Proxy-Setups. Ein HTTP-Client ohne PQC-Fähigkeiten kann den gesamten 
Kommunikationsweg (Client → Proxy → Backend → Client) erfolgreich durchlaufen.

Die Verbindung wurde, wie die Ausgabe SSL connection using TLSv1.3 zeigt, 
mit modernen Sicherheitsstandards aufgebaut. Die Notwendigkeit der -k Option ergibt sich, 
wie im PQC-Client-Test, aus der Testumgebung mit einem selbstsignierten Zertifikat.

In Korrelation mit den Ergebnissen aus dem openssl s_client Test (siehe 2.1) und 
den Nginx-Logs ist nachgewiesen, dass diese erfolgreiche HTTP-Transaktion über 
eine Verbindung lief, deren Sitzungsschlüssel mit einem 
klassischen Key Exchange Mechanism(X25519) gesichert wurde.

## 3. Performance-Analyse des TLS-Handshakes
Um die Performance-Auswirkungen des hybriden PQC-Ansatzes zu quantifizieren, wurde die Anzahl der möglichen TLS-Handshakes pro Sekunde gemessen. Als Testwerkzeug kam `openssl s_time` mit einer Laufzeit von 60 Sekunden pro Testlauf zum Einsatz.

Es wurden zwei Szenarien verglichen:
1.  **Klassischer Handshake:** Ein Client mit einer Standard-System-OpenSSL-Bibliothek, der einen klassischen KEM (ECDHE mit X25519) aushandelt.
2.  **PQC-Handshake:** Ein Client mit einer neueren, PQC-fähigen OpenSSL-Bibliothek, der den hybriden KEM `X25519MLKEM768` aushandelt, was durch die Server-Logs verifiziert wurde.

### 3.1 Messergebnisse
Die durchgeführten Tests ergaben die folgenden Performance-Werte.

| Metrik | Klassischer Handshake (Ältere OpenSSL-Lib) | Hybrider PQC-Handshake (Neuere OpenSSL-Lib) | Veränderung |
| :--- | :--- | :--- | :--- |
| **Gesamte Verbindungen (60s)** | 19,117 | **20,454** | **+7.0 %** |
| **Verbindungen/Sekunde (Real)** | **~313** | **~335** | **+7.0 %** |
| **Durchschnittl. Handshake-Zeit** | ~3.19 ms | **~2.98 ms** | **-6.6 %** |
| **CPU-Zeit pro Handshake** | ~0.58 ms | **~0.43 ms** | **-25.9 %** |

*Tabelle 3.1: Performance-Vergleich von klassischem und hybridem PQC-TLS-Handshake über unterschiedliche OpenSSL-Versionen.*

### 3.2 Analyse und Diskussion
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

---
### Für eine noch tiefere akademische Analyse (Optional)
Um den **reinen Overhead des PQC-Algorithmus** zu isolieren, 
könnten Sie einen dritten Testlauf durchführen:

* **Verwenden Sie den `client-pqc` Container** (mit der neuen OpenSSL-Version).
* **Erzwingen Sie dort aber einen rein klassischen Handshake** (z.B. mit einer Konfigurationsdatei, die `Groups = X25519` setzt).

Wenn Sie dann das Ergebnis von `(PQC auf neuer Lib)` mit `(Klassisch auf neuer Lib)` vergleichen, 
sehen Sie den wahren Performance-Unterschied der Algorithmen selbst, 
ohne den Einfluss der unterschiedlichen Bibliotheksversionen. 
Das wäre eine exzellente Ergänzung für Ihre Arbeit.



