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
openssl s_client -connect nginx-proxy:443 -groups X25519MLKEM768 -tls1_3 -servername pqc.tls.proxy
```

#### 1.1.3 Ergebnis
Der TLS-Handshake wurde erfolgreich abgeschlossen. [Vollständige Ausgabe](testergebnisse/s_client-pq-client.txt)
Die Analyse der Ausgabe von openssl s_client zeigte 
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
dass der für die Sitzung verwendete Schlüssel sowohl auf dem klassischen Elliptic-Curve-Algorithmus X25519 
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

### 1.3 `performance` Test

#### 1.3.1 Ziel

#### 1.3.2 Methode
```bash
openssl s_time -connect nginx-proxy:443 -www / -new -time 60
```
#### 1.3.2 Ergebnis
#### 1.3.3 Analyse

## Testfall 2: Klassischer Client (`client-classic`)

Ziel: Überprüfung, ob der klassische Client eine TLS-Verbindung ohne Post-Quantum Key Exchange Mechanism (KEM) aushandelt.

**Kommandos:**
(Ausgeführt im `client-classic` Container)
```bash
docker-compose exec client-classic bash
```

### 2.1 `openssl s_client` Test

#### 2.1.1 Ziel
#### 2.1.2 Methode
```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername proxy.pqc.test
```

#### 2.1.2 Ergebnis
#### 2.1.3 Analyse

### 2.2 `curl` Test

#### 2.2.1 Ziel
#### 2.2.2 Methode
```bash
curl -v https://nginx-proxy -k
```

#### 2.2.2 Ergebnis
#### 2.2.3 Analyse

### 2.3 `performance` Test

#### 2.3.1 Ziel
#### 2.3.2 Methode
```bash
openssl s_time -connect nginx-proxy:443 -www / -new -time 60
```

#### 2.3.2 Ergebnis
#### 2.3.3 Analyse

## Nginx-Logs der Tests

```bash
docker-compose logs nginx-proxy
```




