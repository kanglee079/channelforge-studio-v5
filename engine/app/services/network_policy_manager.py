"""Network Policy Manager — Egress policy resolver per job type + workspace.

Quyết định routing: DIRECT / WORKSPACE_ROUTE / BLOCK dựa trên job type.
Verify route, check outbound IP, log policy decisions.
"""

from __future__ import annotations

import logging
from ..db import get_conn
from ..utils import utc_now_iso

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════
# Policy Table — job_type → default policy_mode
# ═══════════════════════════════════════════════════════════

POLICY_TABLE: dict[str, str] = {
    # DIRECT — local processing, no account context needed
    "trend_ingest": "DIRECT",
    "generic_scrape_public": "DIRECT",
    "render_video": "DIRECT",
    "embed_asset": "DIRECT",
    "transcribe_audio": "DIRECT",
    "generate_script": "DIRECT",
    "generate_thumbnail": "DIRECT",
    "research_snapshot": "DIRECT",
    "index_rebuild": "DIRECT",
    "analytics_aggregation": "DIRECT",

    # WORKSPACE_ROUTE — requires account context / channel browser
    "open_studio": "WORKSPACE_ROUTE",
    "verify_session": "WORKSPACE_ROUTE",
    "youtube_upload": "WORKSPACE_ROUTE",
    "youtube_metadata_edit": "WORKSPACE_ROUTE",
    "delete_video_from_channel": "WORKSPACE_ROUTE",
    "channel_check": "WORKSPACE_ROUTE",

    # BLOCK — sensitive without valid route
    "unknown_sensitive": "BLOCK",
}


class NetworkPolicyManager:
    """Resolve network policy for each job, verify routes, log decisions."""

    def resolve_policy(self, job_type: str, workspace_id: int = 0, job_id: int = 0) -> dict:
        """Resolve which network policy to apply for a given job.

        Returns:
            dict with: policy_mode, decision, route_profile_id, reason
        """
        base_policy = POLICY_TABLE.get(job_type, "BLOCK")

        # DIRECT jobs — always allow, no route needed
        if base_policy == "DIRECT":
            result = {
                "policy_mode": "DIRECT",
                "decision": "allow",
                "route_profile_id": 0,
                "outbound_ip": "",
                "reason": f"Job type '{job_type}' uses direct local processing",
            }
            self._record_event(workspace_id, job_id, job_type, result)
            return result

        # WORKSPACE_ROUTE jobs — need valid workspace + route
        if base_policy == "WORKSPACE_ROUTE":
            if workspace_id <= 0:
                result = {
                    "policy_mode": "BLOCK",
                    "decision": "block",
                    "route_profile_id": 0,
                    "outbound_ip": "",
                    "reason": f"Job type '{job_type}' requires workspace route but no workspace provided",
                }
                self._record_event(workspace_id, job_id, job_type, result)
                return result

            # Check route binding
            route_info = self._get_active_route(workspace_id)
            if route_info:
                result = {
                    "policy_mode": "WORKSPACE_ROUTE",
                    "decision": "allow",
                    "route_profile_id": route_info["route_profile_id"],
                    "outbound_ip": "",
                    "reason": f"Routed via workspace #{workspace_id} route profile #{route_info['route_profile_id']}",
                }
            else:
                # Fail-closed: no route binding → BLOCK
                # Workspace must explicitly bind a route or set allow_unrouted=1
                allow_unrouted = self._check_allow_unrouted(workspace_id)
                if allow_unrouted:
                    result = {
                        "policy_mode": "WORKSPACE_ROUTE",
                        "decision": "allow_direct_override",
                        "route_profile_id": 0,
                        "outbound_ip": "",
                        "reason": f"Workspace #{workspace_id} has no route but allow_unrouted is enabled — using direct",
                    }
                else:
                    result = {
                        "policy_mode": "BLOCK",
                        "decision": "block",
                        "route_profile_id": 0,
                        "outbound_ip": "",
                        "reason": f"Workspace #{workspace_id} has no route binding — bind a route or enable allow_unrouted",
                    }

            self._record_event(workspace_id, job_id, job_type, result)
            return result

        # BLOCK
        result = {
            "policy_mode": "BLOCK",
            "decision": "block",
            "route_profile_id": 0,
            "outbound_ip": "",
            "reason": f"Job type '{job_type}' is blocked by default policy",
        }
        self._record_event(workspace_id, job_id, job_type, result)
        return result

    def verify_route(self, workspace_id: int) -> dict:
        """Verify that workspace's route binding is healthy and reachable."""
        route_info = self._get_active_route(workspace_id)
        if not route_info:
            return {"ok": False, "message": "Không có route binding hoạt động", "verified": False}

        conn = get_conn()
        proxy = conn.execute("SELECT * FROM proxy_profiles WHERE id=?", (route_info["route_profile_id"],)).fetchone()
        if not proxy:
            return {"ok": False, "message": "Route profile không tồn tại", "verified": False}

        proxy_url = f"{proxy['protocol']}://{proxy['server']}:{proxy['port']}"
        if proxy["username"]:
            proxy_url = f"{proxy['protocol']}://{proxy['username']}:{proxy['password_encrypted']}@{proxy['server']}:{proxy['port']}"

        outbound_ip = self.get_outbound_ip_via_route(proxy_url)
        verified = bool(outbound_ip)

        result = {
            "ok": verified,
            "message": f"Route verified — IP: {outbound_ip}" if verified else "Route verification failed",
            "verified": verified,
            "outbound_ip": outbound_ip,
            "proxy_server": proxy["server"],
        }

        # Log the verification
        self._record_event(workspace_id, 0, "verify_route", {
            "policy_mode": "WORKSPACE_ROUTE",
            "decision": "verified" if verified else "failed",
            "route_profile_id": route_info["route_profile_id"],
            "outbound_ip": outbound_ip,
            "reason": result["message"],
        })

        return result

    def get_outbound_ip_via_route(self, proxy_url: str) -> str:
        """Check outbound IP through a proxy route. Returns IP string or empty."""
        try:
            import urllib.request
            import json
            proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            response = opener.open("http://httpbin.org/ip", timeout=10)
            data = json.loads(response.read())
            return data.get("origin", "")
        except Exception:
            return ""

    def get_network_events(self, workspace_id: int = 0, limit: int = 50) -> list[dict]:
        """Get network policy event log."""
        conn = get_conn()
        if workspace_id > 0:
            rows = conn.execute(
                "SELECT * FROM network_policy_events WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
                (workspace_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM network_policy_events ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Route bindings ─────────────────────────────────────────

    def bind_route(self, workspace_id: int, route_profile_id: int, bind_mode: str = "studio_only", notes: str = "") -> dict:
        """Bind a route profile to a workspace."""
        now = utc_now_iso()
        conn = get_conn()

        # Deactivate existing bindings
        conn.execute("UPDATE workspace_route_bindings SET active=0, updated_at=? WHERE workspace_id=? AND active=1", (now, workspace_id))

        # Create new binding
        conn.execute(
            "INSERT INTO workspace_route_bindings (workspace_id, route_profile_id, bind_mode, active, notes, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?, ?)",
            (workspace_id, route_profile_id, bind_mode, notes, now, now),
        )
        conn.commit()
        return {"ok": True, "message": f"Route profile #{route_profile_id} đã gán vào workspace #{workspace_id}"}

    def unbind_route(self, workspace_id: int) -> dict:
        """Remove active route binding from workspace."""
        now = utc_now_iso()
        conn = get_conn()
        conn.execute("UPDATE workspace_route_bindings SET active=0, updated_at=? WHERE workspace_id=? AND active=1", (now, workspace_id))
        conn.commit()
        return {"ok": True, "message": f"Đã gỡ route binding cho workspace #{workspace_id}"}

    def get_route_binding(self, workspace_id: int) -> dict | None:
        """Get active route binding for a workspace."""
        return self._get_active_route(workspace_id)

    # ── Internal helpers ───────────────────────────────────────

    def _get_active_route(self, workspace_id: int) -> dict | None:
        conn = get_conn()
        row = conn.execute(
            "SELECT * FROM workspace_route_bindings WHERE workspace_id=? AND active=1 ORDER BY created_at DESC LIMIT 1",
            (workspace_id,),
        ).fetchone()
        return dict(row) if row else None

    def _check_allow_unrouted(self, workspace_id: int) -> bool:
        """Check if workspace explicitly allows unrouted (direct) connections.

        Workspace must opt-in via channel_automation_policy.notes containing 'allow_unrouted'
        or via a future explicit column. This is a safety measure — by default, workspace
        traffic to YouTube MUST go through a bound route.
        """
        conn = get_conn()
        try:
            row = conn.execute(
                "SELECT notes FROM channel_automation_policy WHERE workspace_id=?",
                (workspace_id,),
            ).fetchone()
            if row and row["notes"] and "allow_unrouted" in row["notes"].lower():
                return True
        except Exception:
            pass
        return False

    def _record_event(self, workspace_id: int, job_id: int, job_type: str, decision: dict):
        """Record a network policy decision event."""
        now = utc_now_iso()
        conn = get_conn()
        try:
            import json
            evidence = json.dumps({"reason": decision.get("reason", "")})
            conn.execute(
                "INSERT INTO network_policy_events (workspace_id, job_id, job_type, policy_mode, route_profile_id, decision, outbound_ip, evidence_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (workspace_id, job_id, job_type, decision["policy_mode"], decision.get("route_profile_id", 0),
                 decision["decision"], decision.get("outbound_ip", ""), evidence, now),
            )
            conn.commit()
        except Exception as e:
            logger.warning("Failed to record policy event: %s", e)


# Module-level singleton
policy_manager = NetworkPolicyManager()
