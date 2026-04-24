"""
Advanced ML Classification Engine
TF-IDF + Random Forest trained on security event corpus
"""
import re
import json
import numpy as np
from typing import Tuple, Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.multiclass import OneVsRestClassifier
from app.models import IncidentType, SeverityLevel

# ─── Training Corpus ──────────────────────────────────────────────────────────
TRAINING_DATA = [
    # Brute Force
    ("500 failed login attempts detected from 192.168.1.100 against admin account", IncidentType.BRUTE_FORCE),
    ("Multiple authentication failures for user root from external IP in 5 minutes", IncidentType.BRUTE_FORCE),
    ("Account locked after 20 invalid password attempts for service account", IncidentType.BRUTE_FORCE),
    ("Password spraying detected targeting multiple accounts from single source", IncidentType.BRUTE_FORCE),
    ("Credential stuffing attack on login portal using leaked email database", IncidentType.BRUTE_FORCE),
    ("SSH brute force attempt detected from 203.0.113.45", IncidentType.BRUTE_FORCE),
    ("RDP brute force 1000 login attempts in 10 minutes", IncidentType.BRUTE_FORCE),
    ("Windows Event ID 4625 multiple failed logon attempts", IncidentType.BRUTE_FORCE),
    ("Kerberos pre-authentication failure repeated for domain accounts", IncidentType.BRUTE_FORCE),
    ("LDAP authentication failure flood from unknown host", IncidentType.BRUTE_FORCE),
    ("VPN portal receiving automated login attempts with common passwords", IncidentType.BRUTE_FORCE),

    # Malware
    ("Trojan detected in C:\\Users\\test\\Downloads\\invoice.exe", IncidentType.MALWARE),
    ("Suspicious process spawning cmd.exe from winword.exe", IncidentType.MALWARE),
    ("Malicious DLL injection detected in svchost.exe", IncidentType.MALWARE),
    ("Backdoor communication to known C2 server 185.234.x.x", IncidentType.MALWARE),
    ("Rootkit behavior detected in kernel modules", IncidentType.MALWARE),
    ("Botnet C2 traffic detected on port 4444", IncidentType.MALWARE),
    ("Keylogger process capturing keystrokes user credentials", IncidentType.MALWARE),
    ("Worm spreading via network shares SMB protocol", IncidentType.MALWARE),
    ("Spyware collecting browser history and exfiltrating data", IncidentType.MALWARE),
    ("Adware modifying browser settings and DNS", IncidentType.MALWARE),
    ("Suspicious PowerShell encoded command execution", IncidentType.MALWARE),
    ("Malicious macro in Office document executing payload", IncidentType.MALWARE),
    ("AV alert malware trojan found quarantined endpoint", IncidentType.MALWARE),

    # Phishing
    ("User clicked suspicious link from phishing email impersonating IT department", IncidentType.PHISHING),
    ("Spear phishing email targeting CFO requesting wire transfer", IncidentType.PHISHING),
    ("Credential harvesting site impersonating Microsoft 365 login page", IncidentType.PHISHING),
    ("Employee received fake invoice email with malicious attachment", IncidentType.PHISHING),
    ("CEO impersonation email sent to finance requesting gift cards", IncidentType.PHISHING),
    ("Phishing campaign detected multiple users reported suspicious email", IncidentType.PHISHING),
    ("Clone phishing legitimate email modified with malicious link", IncidentType.PHISHING),
    ("SMS smishing attack targeting employees mobile credentials", IncidentType.PHISHING),
    ("Vishing phone call impersonating IT support requesting password", IncidentType.PHISHING),
    ("Malicious email attachment with .docx macro downloading payload", IncidentType.PHISHING),

    # Data Exfiltration
    ("Large data transfer 50GB to external IP 203.0.113.x detected", IncidentType.DATA_EXFILTRATION),
    ("Sensitive database dump uploaded to cloud storage without authorization", IncidentType.DATA_EXFILTRATION),
    ("Employee copying customer PII to personal USB drive", IncidentType.DATA_EXFILTRATION),
    ("Unauthorized FTP transfer of financial records to external server", IncidentType.DATA_EXFILTRATION),
    ("DNS tunneling used to exfiltrate data in DNS queries", IncidentType.DATA_EXFILTRATION),
    ("Bulk email with sensitive attachments to external gmail accounts", IncidentType.DATA_EXFILTRATION),
    ("Steganography detected data hidden in image files being uploaded", IncidentType.DATA_EXFILTRATION),
    ("Anomalous after-hours bulk file access and download detected", IncidentType.DATA_EXFILTRATION),
    ("DLP alert customer database records exported to unauthorized location", IncidentType.DATA_EXFILTRATION),
    ("SFTP transfer of source code repository to competitor IP", IncidentType.DATA_EXFILTRATION),

    # Privilege Escalation
    ("User account added to domain admin group without authorization", IncidentType.PRIVILEGE_ESCALATION),
    ("Sudo command executed by non-privileged user gaining root access", IncidentType.PRIVILEGE_ESCALATION),
    ("UAC bypass detected process gaining elevated privileges", IncidentType.PRIVILEGE_ESCALATION),
    ("Pass-the-hash attack used to gain domain controller access", IncidentType.PRIVILEGE_ESCALATION),
    ("Mimikatz credential dump detected extracting LSASS memory", IncidentType.PRIVILEGE_ESCALATION),
    ("Token impersonation attack escalating from service account to admin", IncidentType.PRIVILEGE_ESCALATION),
    ("Scheduled task created with SYSTEM privileges by regular user", IncidentType.PRIVILEGE_ESCALATION),
    ("Windows privilege escalation CVE exploit detected", IncidentType.PRIVILEGE_ESCALATION),
    ("Unauthorized modification of sudoers file", IncidentType.PRIVILEGE_ESCALATION),
    ("Service account granted domain admin during off-hours", IncidentType.PRIVILEGE_ESCALATION),

    # Ransomware
    ("Files encrypted with .locked extension ransom note README.txt found", IncidentType.RANSOMWARE),
    ("WannaCry ransomware spreading across network shares", IncidentType.RANSOMWARE),
    ("Ryuk ransomware detected encrypting backup files", IncidentType.RANSOMWARE),
    ("Ransomware payment demand $500000 bitcoin displayed on screen", IncidentType.RANSOMWARE),
    ("Shadow copy deletion vssadmin detected before file encryption", IncidentType.RANSOMWARE),
    ("Crypto locker variant detected encrypting financial documents", IncidentType.RANSOMWARE),
    ("Mass file extension change to .encrypted across network drives", IncidentType.RANSOMWARE),
    ("REvil ransomware double extortion data stolen and encrypted", IncidentType.RANSOMWARE),
    ("Backup systems targeted first then file servers encrypted", IncidentType.RANSOMWARE),
    ("Conti ransomware group indicators of compromise detected", IncidentType.RANSOMWARE),

    # DoS/DDoS
    ("Network flooded with 10Gbps UDP traffic from multiple sources", IncidentType.DOS_DDOS),
    ("Web server unavailable due to HTTP flood 100000 requests per second", IncidentType.DOS_DDOS),
    ("SYN flood attack saturating firewall connection table", IncidentType.DOS_DDOS),
    ("Amplification attack using DNS servers targeting our IP", IncidentType.DOS_DDOS),
    ("Application layer DDoS slowloris attack exhausting web server threads", IncidentType.DOS_DDOS),
    ("NTP amplification attack volumetric flooding bandwidth", IncidentType.DOS_DDOS),
    ("Botnet DDOS attack 50000 infected hosts targeting infrastructure", IncidentType.DOS_DDOS),
    ("Service unavailable 503 errors due to traffic overload", IncidentType.DOS_DDOS),

    # Insider Threat
    ("Terminated employee account still active accessing systems after offboarding", IncidentType.INSIDER_THREAT),
    ("Disgruntled employee downloading competitor sensitive documents before resignation", IncidentType.INSIDER_THREAT),
    ("IT admin abusing privileged access to access HR salary database", IncidentType.INSIDER_THREAT),
    ("Employee accessing files outside their department after hours repeatedly", IncidentType.INSIDER_THREAT),
    ("Internal user selling customer data to third party detected", IncidentType.INSIDER_THREAT),
    ("Contractor accessing systems beyond their project scope", IncidentType.INSIDER_THREAT),
    ("Suspicious internal reconnaissance scanning company network resources", IncidentType.INSIDER_THREAT),
    ("Employee violating acceptable use policy installing unauthorized software", IncidentType.INSIDER_THREAT),
]

# ─── Severity indicators ──────────────────────────────────────────────────────
SEVERITY_KEYWORDS = {
    SeverityLevel.CRITICAL: [
        "ransomware", "domain controller", "critical system", "production down", "data breach",
        "pii exposed", "healthcare", "financial records", "all systems", "widespread",
        "c2 communication", "rootkit", "mimikatz", "lsass", "shadow copy deleted"
    ],
    SeverityLevel.HIGH: [
        "admin account", "service account", "privilege escalation", "bulk download",
        "database dump", "external transfer", "backdoor", "persistence", "lateral movement"
    ],
    SeverityLevel.MEDIUM: [
        "suspicious", "potential", "unusual", "repeated", "multiple attempts",
        "anomalous", "policy violation", "unauthorized access"
    ],
    SeverityLevel.LOW: [
        "test", "sandbox", "low priority", "informational", "dev environment", "single attempt"
    ],
}

# Windows Event ID → Incident Type mapping
WINDOWS_EVENT_MAP = {
    4625: (IncidentType.BRUTE_FORCE, "Failed login attempt - Event ID 4625"),
    4771: (IncidentType.BRUTE_FORCE, "Kerberos pre-authentication failed - Event ID 4771"),
    4776: (IncidentType.BRUTE_FORCE, "NTLM authentication failure - Event ID 4776"),
    1102: (IncidentType.INSIDER_THREAT, "Audit log cleared - Event ID 1102"),
    4688: (IncidentType.MALWARE, "Suspicious process created - Event ID 4688"),
    7045: (IncidentType.MALWARE, "New service installed - Event ID 7045"),
    4720: (IncidentType.PRIVILEGE_ESCALATION, "User account created - Event ID 4720"),
    4728: (IncidentType.PRIVILEGE_ESCALATION, "Member added to security group - Event ID 4728"),
    4732: (IncidentType.PRIVILEGE_ESCALATION, "Member added to local admin group - Event ID 4732"),
    4756: (IncidentType.PRIVILEGE_ESCALATION, "Member added to universal security group - Event ID 4756"),
    4663: (IncidentType.DATA_EXFILTRATION, "Object access attempt - Event ID 4663"),
    5156: (IncidentType.DATA_EXFILTRATION, "Network connection allowed - Event ID 5156"),
    4670: (IncidentType.PRIVILEGE_ESCALATION, "Permissions on object changed - Event ID 4670"),
    4698: (IncidentType.INSIDER_THREAT, "Scheduled task created - Event ID 4698"),
    4985: (IncidentType.MALWARE, "State of transaction changed - Event ID 4985"),
}

# Suspicious process names
SUSPICIOUS_PROCESSES = {
    "mimikatz.exe": (IncidentType.PRIVILEGE_ESCALATION, 95),
    "wce.exe": (IncidentType.PRIVILEGE_ESCALATION, 90),
    "pwdump.exe": (IncidentType.PRIVILEGE_ESCALATION, 90),
    "fgdump.exe": (IncidentType.PRIVILEGE_ESCALATION, 88),
    "netcat.exe": (IncidentType.MALWARE, 75),
    "nc.exe": (IncidentType.MALWARE, 70),
    "nmap.exe": (IncidentType.INSIDER_THREAT, 60),
    "psexec.exe": (IncidentType.MALWARE, 65),
    "meterpreter": (IncidentType.MALWARE, 95),
    "cobalt": (IncidentType.MALWARE, 92),
    "cobaltstrike": (IncidentType.MALWARE, 95),
    "tor.exe": (IncidentType.DATA_EXFILTRATION, 70),
    "wscript.exe": (IncidentType.MALWARE, 55),
    "cscript.exe": (IncidentType.MALWARE, 55),
}

# Suspicious network ports
SUSPICIOUS_PORTS = {
    4444: (IncidentType.MALWARE, "Metasploit default shell port"),
    5555: (IncidentType.MALWARE, "Common backdoor port"),
    6666: (IncidentType.MALWARE, "IRC/botnet port"),
    1337: (IncidentType.MALWARE, "Common hacker port"),
    31337: (IncidentType.MALWARE, "Elite backdoor port"),
    12345: (IncidentType.MALWARE, "Common trojan port"),
    9001: (IncidentType.DATA_EXFILTRATION, "Tor port"),
    9050: (IncidentType.DATA_EXFILTRATION, "Tor SOCKS port"),
}


class AdvancedMLEngine:
    """
    ML-based security incident classifier using TF-IDF + Random Forest.
    Trained on security event corpus with 80+ labeled examples.
    """

    def __init__(self):
        self.label_encoder = LabelEncoder()
        self.pipeline = None
        self._trained = False
        self._train()

    def _train(self):
        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1].value for item in TRAINING_DATA]

        encoded_labels = self.label_encoder.fit_transform(labels)

        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=5000,
                sublinear_tf=True,
                strip_accents='unicode',
                analyzer='word',
                min_df=1,
                stop_words='english',
            )),
            ('clf', RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_split=2,
                random_state=42,
                n_jobs=-1,
            )),
        ])
        self.pipeline.fit(texts, encoded_labels)
        self._trained = True

    def classify(self, text: str, event_type: str = "") -> Tuple[IncidentType, float, str]:
        """
        ML classification returning (incident_type, confidence, reasoning).
        """
        combined = f"{text} {event_type}".strip()

        # Get probabilities
        proba = self.pipeline.predict_proba([combined])[0]
        top_idx = int(np.argmax(proba))
        confidence = float(proba[top_idx])
        predicted_label = self.label_encoder.inverse_transform([top_idx])[0]

        # Map back to enum
        try:
            incident_type = IncidentType(predicted_label)
        except ValueError:
            incident_type = IncidentType.UNKNOWN
            confidence = 0.3

        # Get top 3 contributing classes
        sorted_idx = np.argsort(proba)[::-1][:3]
        top_classes = [
            f"{self.label_encoder.inverse_transform([i])[0]} ({proba[i]:.0%})"
            for i in sorted_idx if proba[i] > 0.05
        ]

        reasoning = (
            f"ML classifier ({confidence:.0%} confidence). "
            f"Top candidates: {', '.join(top_classes)}."
        )

        # Fallback to rule-based if confidence is low
        if confidence < 0.45:
            from app.ai_engine import classify_incident as rule_classify
            rule_type, rule_conf, rule_reason = rule_classify(text, event_type)
            if rule_conf > confidence:
                return rule_type, rule_conf, f"[Rule-based fallback] {rule_reason}"

        return incident_type, confidence, reasoning

    def classify_by_event_id(self, event_id: int) -> Optional[Tuple[IncidentType, str]]:
        return WINDOWS_EVENT_MAP.get(event_id)

    def check_suspicious_process(self, process_name: str) -> Optional[Tuple[IncidentType, int]]:
        lower = process_name.lower()
        for proc, info in SUSPICIOUS_PROCESSES.items():
            if proc in lower:
                return info
        return None

    def check_suspicious_port(self, port: int) -> Optional[Tuple[IncidentType, str]]:
        return SUSPICIOUS_PORTS.get(port)

    def assess_severity_from_text(self, text: str) -> Tuple[float, SeverityLevel]:
        """Score-based severity from keyword matching."""
        lower = text.lower()
        scores = {}
        for level, keywords in SEVERITY_KEYWORDS.items():
            hit = sum(1 for kw in keywords if kw in lower)
            if hit > 0:
                scores[level] = hit

        if not scores:
            return 50.0, SeverityLevel.MEDIUM

        best_level = max(scores, key=scores.get)
        level_scores = {
            SeverityLevel.CRITICAL: 85,
            SeverityLevel.HIGH: 68,
            SeverityLevel.MEDIUM: 50,
            SeverityLevel.LOW: 25,
        }
        return float(level_scores[best_level]), best_level

    def compute_anomaly_score(self, metrics: Dict) -> float:
        """
        Compute a behavioural anomaly score (0-100) from system metrics.
        """
        score = 0.0

        cpu = metrics.get("cpu_percent", 0)
        if cpu > 90: score += 30
        elif cpu > 75: score += 15
        elif cpu > 60: score += 5

        mem = metrics.get("memory_percent", 0)
        if mem > 90: score += 25
        elif mem > 80: score += 12

        conns = metrics.get("suspicious_connections", 0)
        score += min(conns * 15, 40)

        suspicious_procs = metrics.get("suspicious_processes", 0)
        score += min(suspicious_procs * 20, 40)

        failed_logins = metrics.get("failed_logins_1h", 0)
        if failed_logins > 50: score += 30
        elif failed_logins > 10: score += 15
        elif failed_logins > 3: score += 5

        return round(min(score, 100), 2)


# Singleton instance
ml_engine = AdvancedMLEngine()
