import json
from datetime import timedelta
import urllib.parse
import urllib.request

from django.utils import timezone

from apps.fleet.models import Vehicle, TelematicsPing
from apps.reports.services import create_accounting_export
from apps.settings_app.models import IntegrationSyncLog


def _http_json(method: str, url: str, *, token: str = "", payload: dict | None = None, timeout: int = 30) -> dict:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, method=method.upper(), headers=headers, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def run_accounting_sync(*, profile, branch=None, period: str = "monthly") -> dict:
    exports = []
    pushed = 0
    errors: list[str] = []

    for export_type in ["INVOICES", "PAYMENTS", "EXPENSES"]:
        result = create_accounting_export(
            provider="QUICKBOOKS" if "QUICKBOOKS" in profile.integration_type else "ZOHO",
            export_type=export_type,
            period=period,
            branch=branch,
        )
        exports.append({"type": export_type, "rows": result["row_count"], "file_name": result["file_name"]})

        if profile.base_url and profile.get_access_token():
            try:
                target = profile.base_url.rstrip("/") + "/imports/accounting"
                _http_json(
                    "POST",
                    target,
                    token=profile.get_access_token(),
                    payload={
                        "export_type": export_type,
                        "period": period,
                        "file_name": result["file_name"],
                        "csv": result["csv"],
                    },
                )
                pushed += 1
            except Exception as exc:
                errors.append(f"{export_type}: {exc}")

    imported = {"customers": 0, "invoices": 0, "payments": 0}
    if profile.base_url and profile.get_access_token():
        try:
            from_date = (timezone.localdate() - timedelta(days=30)).isoformat()
            target = profile.base_url.rstrip("/") + "/exports/ledger"
            remote = _http_json(
                "GET",
                f"{target}?{urllib.parse.urlencode({'from': from_date})}",
                token=profile.get_access_token(),
            )
            imported["customers"] = len(remote.get("customers", []))
            imported["invoices"] = len(remote.get("invoices", []))
            imported["payments"] = len(remote.get("payments", []))
        except Exception as exc:
            errors.append(f"import: {exc}")

    status = "SUCCESS" if not errors else ("PARTIAL" if pushed > 0 else "FAILED")
    summary = f"exports={len(exports)} pushed={pushed} imported={sum(imported.values())}"
    details = {"exports": exports, "pushed": pushed, "imported": imported, "errors": errors}

    IntegrationSyncLog.objects.create(
        profile=profile,
        direction="BIDIRECTIONAL",
        status=status,
        summary=summary,
        details=details,
    )
    return {"status": status, "summary": summary, "details": details}


def run_telematics_pull(*, profile, since_hours: int = 6) -> dict:
    since = timezone.now() - timedelta(hours=max(since_hours, 1))
    created = 0
    errors: list[str] = []

    if not profile.base_url or not profile.get_access_token():
        IntegrationSyncLog.objects.create(
            profile=profile,
            direction="IMPORT",
            status="FAILED",
            summary="Telematics profile missing base_url/access_token",
            details={},
        )
        return {"status": "FAILED", "created": 0, "errors": ["Missing base_url or access_token"]}

    try:
        target = profile.base_url.rstrip("/") + "/telematics/pings"
        remote = _http_json(
            "GET",
            f"{target}?{urllib.parse.urlencode({'since': since.isoformat()})}",
            token=profile.get_access_token(),
        )
        rows = remote.get("results", [])
        for row in rows:
            vehicle_id = row.get("vehicle_id")
            if not vehicle_id:
                continue
            vehicle = Vehicle.objects.filter(id=vehicle_id).first()
            if not vehicle:
                continue
            TelematicsPing.objects.create(
                vehicle=vehicle,
                provider="GPS_PROVIDER_A" if "PROVIDER_A" in profile.integration_type else "GPS_PROVIDER_B",
                external_vehicle_id=str(row.get("external_vehicle_id") or ""),
                recorded_at=row.get("recorded_at") or timezone.now(),
                latitude=row.get("latitude"),
                longitude=row.get("longitude"),
                speed_kmh=row.get("speed_kmh") or 0,
                odometer_km=row.get("odometer_km") or 0,
                fuel_percent=row.get("fuel_percent") or 0,
                fuel_used_liters=row.get("fuel_used_liters") or 0,
                idle_seconds=row.get("idle_seconds") or 0,
                engine_on=row.get("engine_on"),
                engine_status=str(row.get("engine_status") or ""),
                battery_voltage=row.get("battery_voltage"),
                fault_codes=row.get("fault_codes") or [],
                metadata={"source": "integration_pull"},
            )
            created += 1
    except Exception as exc:
        errors.append(str(exc))

    status = "SUCCESS" if not errors else ("PARTIAL" if created > 0 else "FAILED")
    summary = f"telematics imported={created}"
    IntegrationSyncLog.objects.create(
        profile=profile,
        direction="IMPORT",
        status=status,
        summary=summary,
        details={"created": created, "errors": errors},
    )
    return {"status": status, "created": created, "errors": errors}
