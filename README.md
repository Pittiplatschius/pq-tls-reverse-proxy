# Testprotokoll: Hybrider PQC Nginx Reverse Proxy

Dieses Dokument protokolliert die Testergebnisse des hybriden Post-Quantum Nginx Reverse Proxy Setups.

**Datum des Tests:** 27.05.2025

**Testumgebung:**
* Nginx-Proxy-Hostname (intern): `nginx-proxy`
* Zertifikat CN / Servername für SNI: `pqc.tls.proxy`
* PQC-KEM (erwartet): `X25519MLKEM768`
* OpenSSL-Version (PQC-Client): [3.5.0 - aktuellste Version]
* OpenSSL-Version (Klassischer Client): [3.0.2 - System-Standard OpenSSL]

---

## Testfall 1: PQC-fähiger Client (`client-pqc`)

Ziel: Überprüfung, ob der PQC-fähige Client eine TLS-Verbindung mit einem Post-Quantum Key Exchange Mechanism (KEM) aushandelt.

**Kommandos:**
(Ausgeführt im `client-pqc` Container)
```bash
docker-compose exec client-pqc bash
```

### 1.1 `openssl s_client` Test

```bash
openssl s_client -connect nginx-proxy:443 -groups X25519MLKEM768 -tls1_3 -servername pqc.tls.proxy
```

### 1.2 `curl` Test
```bash
curl -v https://nginx-proxy -k
```

### 1.3 erreichbarkeit von Backend

```bash
ping backend-server # Sollte fehlschlagen oder keine Antwort von der Flask-App geben
curl http://backend-server:5000 # Sollte fehlschlagen, da im anderen Netzwerk
```

## Testfall 2: Klassischer Client (`client-classic`)

Ziel: Überprüfung, ob der klassische Client eine TLS-Verbindung ohne Post-Quantum Key Exchange Mechanism (KEM) aushandelt.

**Kommandos:**
(Ausgeführt im `client-classic` Container)
```bash
docker-compose exec client-classic bash
```

### 2.1 `openssl s_client` Test

```bash
openssl s_client -connect nginx-proxy:443 -tls1_3 -servername proxy.pqc.test
```

### 2.2 `curl` Test
```bash
xxx
```

### 2.3 erreichbarkeit von Backend

```bash
ping backend-server # Sollte fehlschlagen oder keine Antwort von der Flask-App geben
curl http://backend-server:5000 # Sollte fehlschlagen, da im anderen Netzwerk
```