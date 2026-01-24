# Security Policy

## Reporting a Vulnerability

I take the security of **Sentient** seriously. If you suspect you have found a vulnerability in the application (Frontend, Backend, or Database), please follow the steps below:

### 1. Private Reporting
**Do NOT open a public GitHub issue.** Public issues alert potential attackers before I have a chance to fix the problem.

Instead, please send a detailed report via email to:
**jessengolab.dev@gmail.com**

### 2. What to Include
To help me triage and fix the issue quickly, please include:
* **Type of Issue:** (e.g., SQL Injection, XSS, Auth Bypass)
* **Full paths/URLs:** affected endpoints (e.g., `/api/auth/check`).
* **Proof of Concept:** Step-by-step instructions to reproduce the vulnerability.
* **Impact:** What data or access can be compromised?

### 3. My Response Policy
* **Acknowledgement:** I will respond to your report within **48 hours**.
* **Assessment:** I will confirm the vulnerability and determine its severity.
* **Fix:** I will prioritize a fix and release a patch as soon as possible.
* **Disclosure:** I will coordinate a public disclosure with you only *after* the fix has been deployed.

## Scope

### In Scope
* Authentication & Authorization flaws (e.g., Supabase bypasses).
* Data Leaks (e.g., exposing user email addresses or portfolio data).
* Injection Attacks (SQLi, NoSQLi, Command Injection).
* Cross-Site Scripting (XSS) in the dashboard.

### Out of Scope
* Denial of Service (DoS/DDoS) attacks.
* Social Engineering or Phishing.
* Issues related to third-party providers (Alpaca, Yahoo Finance, Finviz) unless it involves credential leakage from our side.
* UI/UX bugs that do not pose a security risk.

## Security Best Practices
I strive to follow industry standards:
* **Secrets Management:** All API keys are stored in environment variables, never in code.
* **Dependencies:** I use automated tools (like Dependabot) to keep packages updated.
* **Authentication:** All user management is handled securely via Supabase Auth.

Thank you for helping keep Sentient safe!