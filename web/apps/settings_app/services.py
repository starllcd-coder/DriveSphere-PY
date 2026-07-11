from __future__ import annotations

from dataclasses import dataclass
import json
import re
from urllib.request import urlopen
from urllib.parse import urlencode
from django.db import connection, transaction
from django.db.utils import OperationalError
from django.utils import timezone

from .models import BusinessProfile, DocumentNumbering, DatabaseProfile


def test_db_connection() -> tuple[bool, str]:
    """
    Tests CURRENT Django connection.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        return True, "Connection Successful."
    except OperationalError as e:
        return False, f"Connection Failed: {e}"
    except Exception as e:
        return False, f"Connection Error: {e}"


@transaction.atomic
def _derive_branch_code(branch_name: str | None) -> str:
    if not branch_name:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", branch_name).strip()
    if not cleaned:
        return ""
    first_word = cleaned.split()[0].upper()
    consonants = re.sub(r"[AEIOU]", "", first_word)
    if len(consonants) >= 3:
        # first consonant + last two consonants (e.g., Muscat -> MCT)
        return (consonants[0] + consonants[-2:])[:3]
    if len(first_word) <= 3:
        return first_word
    return first_word[:3]


def _derive_company_code(business_name: str | None) -> str:
    if not business_name:
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9 ]+", " ", business_name).strip()
    if not cleaned:
        return ""
    parts = cleaned.split()
    if len(parts) >= 2:
        return "".join(p[0] for p in parts)[:4].upper()
    return cleaned[:4].upper()


def _derive_doc_code(doc_type: str) -> str:
    lookup = {
        "INVOICE": "INV",
        "RECEIPT": "RCT",
        "AGREEMENT": "AGR",
        "CONFIRMATION": "CNF",
        "QUOTATION": "QTN",
        "HANDOVER": "HND",
        "RETURN_REPORT": "RR",
        "REPORT": "RPT",
    }
    key = (doc_type or "").strip().upper()
    if key in lookup:
        return lookup[key]
    cleaned = re.sub(r"[^A-Za-z0-9]+", " ", key).strip()
    if not cleaned:
        return "DOC"
    parts = cleaned.split()
    if len(parts) >= 2:
        return "".join(p[0] for p in parts)[:4].upper()
    return cleaned[:4].upper()


@transaction.atomic
def get_next_document_number(
    doc_type: str,
    branch_name: str | None = None,
    branch_code: str | None = None,
    for_date=None,
) -> str:
    """
    Atomic increment for document numbers (Invoice/Receipt/Agreement/Reports/etc).
    """
    dn = DocumentNumbering.objects.select_for_update().filter(doc_type=doc_type).first()
    if not dn:
        dn = DocumentNumbering.objects.create(
            doc_type=doc_type,
            doc_code=_derive_doc_code(doc_type),
            prefix="DS",
            separator="-",
            padding=6,
            next_number=1,
        )

    num = str(dn.next_number).zfill(dn.padding)
    sep = dn.separator or "-"
    date_str = (for_date or timezone.localdate()).strftime("%Y%m%d")
    business = BusinessProfile.get_solo()
    company_code = (business.short_code or "").strip().upper() or (dn.prefix or "").strip().upper() or _derive_company_code(business.business_name) or "DS"
    doc_code = (dn.doc_code or "").strip().upper() or _derive_doc_code(doc_type)
    branch_part = (branch_code or "").strip().upper() or _derive_branch_code(branch_name) or "ALL"

    parts = [company_code, branch_part, doc_code, date_str, num]
    value = sep.join(parts)

    dn.next_number += 1
    dn.save(update_fields=["next_number"])
    return value


def save_database_profile(data: dict) -> DatabaseProfile:
    prof = DatabaseProfile.get_solo()
    prof.provider = data.get("provider", prof.provider)
    prof.host = data.get("host", prof.host)
    prof.port = int(data.get("port", prof.port or 5432))
    prof.database_name = data.get("database_name", prof.database_name)
    prof.username = data.get("username", prof.username)
    if "password" in data:
        incoming_password = data.get("password")
        if incoming_password:
            prof.set_password(str(incoming_password))
    prof.sslmode = data.get("sslmode", prof.sslmode)
    prof.is_active = bool(data.get("is_active", prof.is_active))
    prof.save()
    return prof


def get_database_profile() -> DatabaseProfile:
    return DatabaseProfile.get_solo()


@dataclass
class DbTestResult:
    ok: bool
    message: str


def test_target_db_connection(profile: DatabaseProfile) -> DbTestResult:
    """
    Tests DB credentials stored in DatabaseProfile (Postgres/Neon) using psycopg.
    """
    try:
        import psycopg

        conn = psycopg.connect(
            host=profile.host,
            port=profile.port,
            dbname=profile.database_name,
            user=profile.username,
            password=profile.get_password(),
            sslmode=profile.sslmode or "require",
            connect_timeout=5,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        conn.close()
        return DbTestResult(ok=True, message="Target Connection Successful.")
    except Exception as e:
        return DbTestResult(ok=False, message=f"Target Connection Failed: {e}")


def migrate_sqlite_to_target_placeholder(profile: DatabaseProfile) -> DbTestResult:
    """
    Placeholder: data migration from SQLite -> PostgreSQL/Neon.

    We do NOT execute a live migration here yet because production migration needs:
    - proper environment switch
    - schema migration checks
    - data copy strategy & conflict handling
    - downtime planning
    """
    engine = connection.settings_dict.get("ENGINE", "")
    if "sqlite" not in engine:
        return DbTestResult(ok=False, message="Current DB is not SQLite. Migration placeholder is for SQLite -> Postgres/Neon.")

    if not profile.host or not profile.database_name or not profile.username:
        return DbTestResult(ok=False, message="Database Profile is incomplete. Please fill Host/DB/User.")

    return DbTestResult(
        ok=True,
        message=(
            "Migration Placeholder Ready.\n"
            "Next step: we will add a safe migration command that:\n"
            "1) runs migrations on target\n"
            "2) exports SQLite data\n"
            "3) imports to target in correct order\n"
            "4) validates counts\n"
        ),
    )


@dataclass
class ExchangeRateResult:
    ok: bool
    message: str
    base: str = ""
    rates: dict | None = None


def fetch_exchange_rates(base_code: str) -> ExchangeRateResult:
    base = (base_code or "").strip().upper() or "USD"
    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        with urlopen(url, timeout=10) as res:
            payload = json.loads(res.read().decode("utf-8"))
        if payload.get("result") == "error":
            return ExchangeRateResult(ok=False, message=payload.get("error-type") or "Provider error")

        rates = payload.get("rates") or {}
        if not rates:
            return ExchangeRateResult(ok=False, message="No rates returned from provider.")
        return ExchangeRateResult(ok=True, message="Exchange rates updated.", base=payload.get("base_code") or base, rates=rates)
    except Exception as e:
        return ExchangeRateResult(ok=False, message=f"Failed to fetch rates: {e}")

