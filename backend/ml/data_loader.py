"""
ml/data_loader.py — Dataset loading and label mapping for TicketFlow AI.
Supports Kaggle customer support datasets + synthetic fallback data.
"""

import os
import random
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Optional
from loguru import logger

# ─── 10-domain label mapping ──────────────────────────────────────────
LABEL_MAP: Dict[str, str] = {
    "network": "Network",
    "connectivity": "Network",
    "internet": "Network",
    "vpn": "Network",
    "wifi": "Network",
    "firewall": "Network",
    "authentication": "Auth",
    "login": "Auth",
    "password": "Auth",
    "account access": "Auth",
    "access denied": "Auth",
    "2fa": "Auth",
    "sso": "Auth",
    "mfa": "Auth",
    "locked out": "Auth",
    "software": "Software",
    "application": "Software",
    "app": "Software",
    "bug": "Software",
    "crash": "Software",
    "installation": "Software",
    "update": "Software",
    "upgrade": "Software",
    "hardware": "Hardware",
    "device": "Hardware",
    "laptop": "Hardware",
    "printer": "Hardware",
    "monitor": "Hardware",
    "keyboard": "Hardware",
    "equipment": "Hardware",
    "permission": "Access",
    "access request": "Access",
    "role": "Access",
    "authorization": "Access",
    "grant access": "Access",
    "revoke": "Access",
    "admin rights": "Access",
    "billing": "Billing",
    "payment": "Billing",
    "invoice": "Billing",
    "refund": "Billing",
    "subscription": "Billing",
    "charge": "Billing",
    "transaction": "Billing",
    "email": "Email",
    "mail": "Email",
    "inbox": "Email",
    "outlook": "Email",
    "calendar": "Email",
    "smtp": "Email",
    "communication": "Email",
    "security": "Security",
    "phishing": "Security",
    "malware": "Security",
    "virus": "Security",
    "ransomware": "Security",
    "breach": "Security",
    "compliance": "Security",
    "threat": "Security",
    "service request": "ServiceRequest",
    "new request": "ServiceRequest",
    "provisioning": "ServiceRequest",
    "onboarding": "ServiceRequest",
    "setup": "ServiceRequest",
    "request": "ServiceRequest",
    "database": "Database",
    "server": "Database",
    "sql": "Database",
    "backup": "Database",
    "storage": "Database",
    "cloud": "Database",
    "infrastructure": "Database",
}

ALL_CATEGORIES: List[str] = [
    "Network",
    "Auth",
    "Software",
    "Hardware",
    "Access",
    "Billing",
    "Email",
    "Security",
    "ServiceRequest",
    "Database",
]

ALL_PRIORITIES: List[str] = ["Low", "Medium", "High", "Critical"]


def map_label(raw_label: str) -> Optional[str]:
    """Map a raw dataset label to one of our 10 categories."""
    if not raw_label:
        return None
    label_lower = str(raw_label).lower().strip()
    if label_lower in LABEL_MAP:
        return LABEL_MAP[label_lower]
    for key, category in LABEL_MAP.items():
        if key in label_lower or label_lower in key:
            return category
    return None


# ─── Priority assignment ──────────────────────────────────────────────
def assign_priority(text: str, category: str) -> str:
    text_lower = text.lower()

    # Security — always Critical or High
    if category == "Security":
        if any(
            w in text_lower
            for w in [
                "ransomware",
                "encrypted",
                "breach",
                "stolen",
                "hacked",
                "leaked",
                "compromised",
                "ransom",
                "ddos",
                "critical vulnerability",
            ]
        ):
            return "Critical"
        return "High"

    # Critical — only truly severe cases
    if any(
        w in text_lower
        for w in [
            "production down",
            "all users",
            "whole team",
            "entire company",
            "cannot work",
            "completely down",
            "system down",
            "outage",
            "data loss",
            "100%",
            "critical alert",
            "critical slowdown",
            "deadlock",
            "connection refused",
            "exhausted",
            "corrupted",
            "unstable",
            "memory leak",
        ]
    ):
        return "Critical"

    # High — blocked or broken
    if any(
        w in text_lower
        for w in [
            "urgent",
            "asap",
            "immediately",
            "blocking",
            "blocked",
            "not working",
            "cannot access",
            "locked",
            "failed",
            "down",
            "error",
            "crash",
            "crashing",
            "broken",
        ]
    ):
        return "High"

    # Low — routine polite requests
    if any(
        w in text_lower
        for w in [
            "please provision",
            "please create",
            "please set up",
            "please order",
            "please install",
            "request to create",
            "request for",
            "need a new",
            "new employee",
            "new intern",
            "onboarding",
            "ergonomic",
            "standing desk",
            "when possible",
        ]
    ):
        return "Low"

    # Medium — default for everything else
    return "Medium"


def generate_synthetic_tickets() -> pd.DataFrame:
    """
    Generate high-quality synthetic ticket data — 1000 per category = 10000 total.
    Priority is assigned by keyword rules (not randomly) for better model training.
    """
    templates = {
        "Network": [
            "My VPN is not connecting and I cannot access company resources",
            "Internet connection keeps dropping every few minutes",
            "Cannot ping the internal server, getting timeout errors",
            "WiFi is showing connected but no internet access",
            "DNS resolution failing for internal domains",
            "Firewall blocking outbound connections on port 443",
            "Remote desktop connection drops when using VPN",
            "Network latency is extremely high, pages loading slowly",
            "Cannot access shared network drives from home",
            "VPN authentication keeps failing with correct credentials",
            "No internet connection on my workstation since this morning",
            "VPN keeps disconnecting after 10 minutes of use",
            "Cannot reach the internal wiki site from home network",
            "My IP address changed and now I cannot access internal tools",
            "Proxy settings are blocking access to required websites",
            "Ethernet cable connected but showing limited connectivity",
            "Cannot connect to office WiFi with my laptop",
            "Network drive Z: is not mapping on startup",
            "Ping to google.com is working but internal servers unreachable",
            "Split tunneling not working correctly on company VPN",
            "Port 8080 is being blocked by company firewall",
            "DNS server not responding error on Windows",
            "Cannot access RDP from home despite VPN being connected",
            "Network switch in meeting room not working",
            "Slow internet only on my laptop not others in same area",
        ],
        "Auth": [
            "My account is locked after too many login attempts",
            "Cannot login to the portal, password reset not working",
            "Two-factor authentication code not being sent to my phone",
            "SSO is not redirecting properly, getting error 500",
            "My session keeps timing out every 5 minutes",
            "Cannot generate new API token, getting permission denied",
            "OTP codes from authenticator app not being accepted",
            "Login page gives blank screen after entering credentials",
            "Password reset link expired before I could use it",
            "My account was locked by security policy",
            "Cannot log into my account, forgot password",
            "Login not working, keeps saying invalid credentials",
            "Account disabled without warning, need it reactivated",
            "Microsoft authenticator app showing wrong code",
            "Cannot sign in with Google SSO, redirects to error page",
            "New employee cannot activate their account",
            "Password policy forcing reset but new password not accepted",
            "Biometric login stopped working on company laptop",
            "LDAP authentication failing for legacy application",
            "Active Directory account locked, need unlock",
            "Cannot access any systems, think my account was deleted",
            "Login works on browser but not on mobile app",
            "Token expired immediately after logging in",
            "My colleague's account needs to be reset urgently",
            "Smart card authentication not working at new desk",
        ],
        "Software": [
            "The application crashes every time I try to open a report",
            "Software update failed and now the app won't start",
            "Getting exception error when processing large files",
            "The Excel plugin stopped working after Windows update",
            "Application freezes when multiple users access it simultaneously",
            "License expired message showing even with valid license",
            "Cannot install the new version, getting error code 1603",
            "Application performance degraded significantly after upgrade",
            "Error message unable to connect to database when loading app",
            "The export function throws a null pointer exception",
            "Teams keeps crashing when I try to share my screen",
            "Office 365 apps not opening, showing activation error",
            "Adobe Acrobat will not open PDF files anymore",
            "Python script throwing import error after IT update",
            "Zoom audio not working after recent Windows update",
            "Cannot print from application, driver error message",
            "Application throwing SSL certificate error",
            "Browser extension not working after Chrome update",
            "ERP system very slow when generating reports",
            "Java runtime error when opening finance application",
            "Software installation blocked by group policy",
            "App shows loading forever and never completes",
            "AutoCAD crashes when opening files larger than 50MB",
            "Cannot run the setup wizard, getting admin rights error",
            "New software version missing features from old version",
        ],
        "Hardware": [
            "My laptop screen has flickering lines and is unusable",
            "Keyboard keys are not responding especially the spacebar",
            "Printer is offline and not printing any documents",
            "Battery drains in less than 2 hours even when fully charged",
            "USB ports on my docking station stopped working",
            "External monitor not being detected by my laptop",
            "Laptop overheating and shutting down after 30 minutes",
            "Webcam not recognized by system for video calls",
            "Hard drive making clicking noises files corrupted",
            "Trackpad gestures stopped working after update",
            "My computer will not turn on at all this morning",
            "Blue screen of death appearing randomly",
            "Laptop fan is very loud and running constantly",
            "Power adapter not charging the laptop battery",
            "Screen brightness stuck at maximum cannot adjust",
            "Mouse keeps disconnecting and reconnecting randomly",
            "Docking station not charging laptop when connected",
            "Second monitor showing black screen only",
            "Headset microphone not being detected by computer",
            "Laptop keyboard some keys producing wrong characters",
            "Desktop computer making beeping sounds on startup",
            "USB hub not recognized when plugged into laptop",
            "Touch screen on laptop not responding to touch",
            "Printer printing blank pages despite having ink",
            "Laptop speaker producing no sound even at max volume",
        ],
        "Access": [
            "Need access to the HR system for the new project",
            "Cannot access the shared folder on the network drive",
            "My admin rights were removed without notification",
            "Request to grant read access to the production database",
            "New employee needs system access but account not created",
            "Role permissions need to be updated for team lead",
            "Cannot view confidential salary reports need access",
            "Shared mailbox access was revoked need it restored",
            "Need elevated permissions to install approved software",
            "Contractor account needs temporary access to client portal",
            "I need access to the finance reporting dashboard",
            "Please grant me write access to the project folder",
            "My access to Salesforce was removed after role change",
            "Need read-only access to production database for audit",
            "Team member cannot access SharePoint site for project",
            "Request to add me to the distribution list for reports",
            "Need access to AWS console for deployment work",
            "Cannot access JIRA board for my current project",
            "My Confluence edit permissions were removed",
            "Request elevated access for quarterly system maintenance",
            "Need to access archived emails from departed employee",
            "Cannot access the payroll system despite HR approval",
            "Please add me to the security group for building access",
            "Intern needs temporary access to design tools",
            "Access to API keys needed for integration project",
        ],
        "Billing": [
            "I was charged twice for the monthly subscription",
            "Invoice shows incorrect amount need correction",
            "Refund not processed after 2 weeks of request",
            "Payment method update page is giving error",
            "Subscription did not renew despite active card",
            "Was charged for cancelled service need refund",
            "Invoice missing VAT number required for tax purposes",
            "Cannot download invoice PDF from billing portal",
            "Credit card declined but subscription shows active",
            "Annual subscription not prorated after upgrade",
            "Duplicate charge appeared on my credit card statement",
            "I need an invoice for last months payment for expenses",
            "Billing address on invoice is wrong need to update",
            "Cannot update payment method getting validation error",
            "Was billed for premium plan but on basic plan",
            "Discount code not applied to my subscription",
            "I cancelled subscription but still being charged",
            "Need itemized invoice for accounting department",
            "Payment failed but service was cancelled anyway",
            "Wrong currency being charged on international account",
            "Trial period ended early and charged without notice",
            "Cannot access billing history older than 6 months",
            "Multiple invoices for same period generated",
            "Tax exempt status not reflected in billing",
            "Need to change billing cycle from monthly to annual",
        ],
        "Email": [
            "Emails not syncing to Outlook on mobile device",
            "Cannot send emails getting SMTP server error",
            "All emails going to spam including from colleagues",
            "Calendar invites not showing in Outlook calendar",
            "Inbox showing wrong count emails marked unread incorrectly",
            "Company email signatures disappeared after Outlook update",
            "Cannot add attachment larger than 10MB to emails",
            "Email forwarding rule not working as configured",
            "Shared mailbox not accessible after password change",
            "Out of office reply sending to internal colleagues",
            "Outlook not opening showing cannot start Microsoft Outlook",
            "Emails stuck in outbox not being sent",
            "Cannot receive emails from external domain",
            "Email search not finding recent emails",
            "Outlook calendar not syncing with Teams calendar",
            "Distribution list email bouncing for some recipients",
            "My sent emails are not being saved to sent folder",
            "Cannot set up email on new iPhone",
            "Junk mail filter too aggressive blocking legitimate emails",
            "Cannot recall sent email using recall feature",
            "Email quota full cannot receive new messages",
            "Replies going to wrong address not reply-to address",
            "Meeting invites from Zoom not showing in calendar",
            "Email rules not executing automatically",
            "HTML emails showing as plain text in Outlook",
        ],
        "Security": [
            "I received a suspicious phishing email asking for credentials",
            "Ransomware detected on my machine files are encrypted",
            "Unauthorized login attempt from foreign IP detected",
            "Malware alert from antivirus need immediate assistance",
            "Data breach suspected customer records might be exposed",
            "Suspicious executable found in downloads folder",
            "Corporate credentials were leaked in data breach",
            "Unknown software installed without authorization",
            "Security audit found critical vulnerability in production",
            "Phishing site impersonating our company portal discovered",
            "I accidentally clicked a link in suspicious email",
            "Antivirus found trojan virus on my computer",
            "Someone else logged into my account from another country",
            "I think my computer has been hacked",
            "Suspicious process running in background using high CPU",
            "Company data found on unauthorized external website",
            "Received ransom note on computer screen",
            "USB drive with company data was lost",
            "Employee sharing confidential data via personal email",
            "Crypto mining software found on company machine",
            "Password found in plain text in shared document",
            "Unencrypted laptop with sensitive data was stolen",
            "API keys accidentally committed to public GitHub repo",
            "Suspicious admin account created overnight",
            "DDoS attack suspected on company website",
        ],
        "ServiceRequest": [
            "Please provision a new cloud storage account for the team",
            "New employee joining needs laptop and system setup",
            "Request to create shared mailbox for the support team",
            "Need software license for Adobe Acrobat for design work",
            "Please set up VPN access for the remote contractor",
            "Request to create new project folder with team permissions",
            "New server environment needed for staging deployment",
            "Need onboarding checklist setup for new department",
            "Please create service account for automated processes",
            "Request for mobile device management enrollment",
            "Need a new monitor for my workstation please",
            "Request to upgrade my laptop RAM to 16GB",
            "Please create a new Slack workspace for the team",
            "Need a dedicated phone line for the new office",
            "Request to set up automated backup for project files",
            "New intern starting Monday needs full system access",
            "Please order replacement keyboard for my workstation",
            "Need Zoom Pro license for monthly all-hands meetings",
            "Request for ergonomic chair and standing desk",
            "Please set up conference room AV equipment",
            "Need to provision 5 new user accounts for new hires",
            "Request for dedicated IP address for office",
            "Please install approved security certificate on server",
            "Need USB security key for MFA setup",
            "Request for additional cloud storage quota increase",
        ],
        "Database": [
            "Database server CPU is at 100% causing critical slowdown",
            "SQL queries timing out production application affected",
            "Database backup failed last night need manual run",
            "Disk space on database server at 95% critical alert",
            "Cannot connect to PostgreSQL server connection refused",
            "MySQL replication lag increased to 45 minutes",
            "Memory leak detected in database process server unstable",
            "Database schema migration script failed midway through",
            "Read replicas returning stale data cache not clearing",
            "Database indexes corrupted after unexpected server restart",
            "Production database throwing deadlock errors under load",
            "Slow query log showing multiple queries over 30 seconds",
            "Database connection pool exhausted during peak hours",
            "MongoDB replica set primary election taking too long",
            "Database transaction log file is almost full",
            "Cannot restore database from backup file corrupted",
            "Redis cache not evicting old keys memory full",
            "Database user account locked due to failed connections",
            "Incorrect data returned by stored procedure after update",
            "Database tablespace needs expansion urgently",
            "Scheduled database maintenance job failed silently",
            "Query performance degraded after statistics not updated",
            "Database firewall blocking application server connection",
            "Audit log table growing too fast filling disk",
            "Database version upgrade broke existing stored procedures",
        ],
    }

    prefixes = [
        "",
        "Hi team, ",
        "Hello, ",
        "Urgent: ",
        "Hi IT support, ",
        "Good morning, ",
        "Please help - ",
        "URGENT - ",
        "Hi, ",
        "Dear support, ",
        "Hi helpdesk, ",
        "Hello support team, ",
    ]
    suffixes = [
        "",
        " Please help urgently.",
        " This is affecting my work.",
        " Multiple users are affected.",
        " This has been going on for 3 days.",
        " I need this resolved ASAP.",
        " Can someone look into this?",
        " Similar issue happened last month too.",
        " This is blocking my work completely.",
        " Please prioritize this request.",
        " Happening since yesterday morning.",
        " Our whole team is impacted.",
        " Please respond as soon as possible.",
        " This is a critical blocker.",
        " It was working fine last week.",
        " I already tried restarting.",
        " Tried basic troubleshooting, still broken.",
    ]

    rows = []
    random.seed(42)

    for category, tmpl_list in templates.items():
        for _ in range(1000):
            base = random.choice(tmpl_list)
            prefix = random.choice(prefixes)
            suffix = random.choice(suffixes)
            text = f"{prefix}{base}{suffix}".strip()

            # ── KEY CHANGE: keyword-based priority not random ──────────
            priority = assign_priority(text, category)

            rows.append(
                {
                    "text": text,
                    "category": category,
                    "priority": priority,
                }
            )

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    # Log priority distribution for verification
    logger.info(f"Generated {len(df)} synthetic training samples")
    logger.info(f"Priority distribution: " f"{df['priority'].value_counts().to_dict()}")
    return df


def load_training_data(
    data_dir: Optional[str] = None, use_synthetic: bool = True
) -> pd.DataFrame:
    """
    Load training data from CSV files or generate synthetic data.
    """
    dfs = []

    if data_dir and os.path.exists(data_dir):
        customer_csv = os.path.join(data_dir, "customer_support_tickets.csv")
        if os.path.exists(customer_csv):
            try:
                df_raw = pd.read_csv(customer_csv)
                logger.info(f"Loaded {len(df_raw)} rows from {customer_csv}")
                text_col = next(
                    (
                        c
                        for c in df_raw.columns
                        if "description" in c.lower()
                        or "body" in c.lower()
                        or "text" in c.lower()
                        or "ticket_description" in c.lower()
                    ),
                    None,
                )
                label_col = next(
                    (
                        c
                        for c in df_raw.columns
                        if "type" in c.lower()
                        or "category" in c.lower()
                        or "topic" in c.lower()
                        or "issue_type" in c.lower()
                    ),
                    None,
                )
                if text_col and label_col:
                    df_mapped = pd.DataFrame()
                    df_mapped["text"] = df_raw[text_col].astype(str)
                    df_mapped["raw_label"] = df_raw[label_col].astype(str)
                    df_mapped["category"] = df_mapped["raw_label"].apply(map_label)
                    df_mapped = df_mapped.dropna(subset=["category"])
                    df_mapped["priority"] = "Medium"
                    dfs.append(df_mapped[["text", "category", "priority"]])
                    logger.info(f"Mapped {len(df_mapped)} samples from Kaggle dataset")
            except Exception as e:
                logger.warning(f"Failed to load Kaggle dataset: {e}")

    if use_synthetic or not dfs:
        synthetic_df = generate_synthetic_tickets()
        dfs.append(synthetic_df)

    if not dfs:
        raise ValueError("No training data available.")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.dropna(subset=["text", "category"])
    combined = combined[combined["text"].str.len() > 20]
    combined = combined[combined["category"].isin(ALL_CATEGORIES)]

    logger.info(
        f"Total training samples: {len(combined)} | "
        f"Categories: {combined['category'].value_counts().to_dict()}"
    )
    return combined


def train_val_test_split(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Stratified 70/15/15 split on category column."""
    from sklearn.model_selection import train_test_split

    test_ratio = 1.0 - train_ratio - val_ratio
    train_df, temp_df = train_test_split(
        df,
        test_size=(val_ratio + test_ratio),
        stratify=df["category"],
        random_state=random_state,
    )
    val_size_relative = val_ratio / (val_ratio + test_ratio)
    val_df, test_df = train_test_split(
        temp_df,
        test_size=(1 - val_size_relative),
        stratify=temp_df["category"],
        random_state=random_state,
    )
    logger.info(
        f"Split sizes → train: {len(train_df)}, "
        f"val: {len(val_df)}, test: {len(test_df)}"
    )
    return train_df, val_df, test_df
