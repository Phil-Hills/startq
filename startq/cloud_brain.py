"""
startq.cloud_brain - Cloud Brain Client for A2AC Enterprise
============================================================
Connect your local StartQ brain to a hosted cloud endpoint.
Sessions persist across machines, teams, and IDE crashes.

Uses Python http.client (stdlib) — zero external dependencies.
"""

import http.client
import json
import ssl
import time


class CloudBrainClient:
    """REST client for a hosted Brain endpoint.
    
    Works with any JSON REST backend that implements:
        POST /store     — store a session receipt
        GET  /health    — health check
        POST /search/semantic — search for recent sessions
    """

    def __init__(self, brain_url: str, api_key: str = None, timeout: int = 15):
        self.brain_url = brain_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._ctx = ssl.create_default_context()
        
        # Parse host from URL
        url = self.brain_url
        if url.startswith("https://"):
            self._scheme = "https"
            self._host = url[8:]
        elif url.startswith("http://"):
            self._scheme = "http"
            self._host = url[7:]
        else:
            self._scheme = "https"
            self._host = url
        
        # Strip any path from host
        if "/" in self._host:
            self._host, self._base_path = self._host.split("/", 1)
            self._base_path = "/" + self._base_path
        else:
            self._base_path = ""

    def _connect(self):
        """Create a new connection."""
        if self._scheme == "https":
            return http.client.HTTPSConnection(
                self._host, timeout=self.timeout, context=self._ctx
            )
        return http.client.HTTPConnection(self._host, timeout=self.timeout)

    def _headers(self):
        """Build request headers."""
        h = {
            "Content-Type": "application/json",
            "User-Agent": "startq-cloud/0.3.0",
        }
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _request(self, method: str, path: str, body: dict = None) -> tuple:
        """Make an HTTP request. Returns (status, body_dict)."""
        conn = self._connect()
        full_path = self._base_path + path
        payload = json.dumps(body).encode() if body else None
        
        try:
            conn.request(method, full_path, body=payload, headers=self._headers())
            resp = conn.getresponse()
            data = resp.read().decode()
            conn.close()
            try:
                return resp.status, json.loads(data)
            except (json.JSONDecodeError, ValueError):
                return resp.status, {"raw": data[:500]}
        except Exception as e:
            return 0, {"error": str(e)}

    def health(self) -> bool:
        """Check if the cloud Brain is reachable."""
        status, body = self._request("GET", "/health")
        return status == 200

    def store_session(self, payload: dict) -> str | None:
        """Store a session receipt in the cloud Brain.
        
        Returns the stored session ID, or None on failure.
        """
        status, body = self._request("POST", "/store", payload)
        if status in (200, 201):
            return body.get("id", body.get("session_id", "stored"))
        return None

    def load_latest(self, identity: str = None) -> dict | None:
        """Load the most recent session context from the cloud Brain.
        
        Searches for session_receipt type cubes and returns the latest.
        """
        query = "session_receipt endq"
        if identity:
            query += f" {identity}"
        
        status, body = self._request("POST", "/search/semantic", {
            "query": query,
            "limit": 1,
        })
        
        if status == 200:
            results = body.get("results", body.get("cubes", []))
            if results:
                return results[0]
        return None

    def sync_session(self, local_payload: dict) -> dict:
        """Full sync: store locally-created session to cloud.
        
        Returns a receipt dict with sync status.
        """
        receipt = {
            "synced": False,
            "cloud_id": None,
            "error": None,
        }
        
        try:
            cloud_id = self.store_session(local_payload)
            if cloud_id:
                receipt["synced"] = True
                receipt["cloud_id"] = cloud_id
            else:
                receipt["error"] = "Store returned None"
        except Exception as e:
            receipt["error"] = str(e)
        
        return receipt
