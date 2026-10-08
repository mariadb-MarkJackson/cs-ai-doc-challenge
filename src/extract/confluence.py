"""Minimal Confluence Cloud REST client (read-only)."""
import requests

from src import config

PAGE_EXPAND = "body.storage,version,metadata.labels,space,ancestors"


class ConfluenceClient:
    def __init__(self):
        env = config.require(
            "CONFLUENCE_BASE_URL", "CONFLUENCE_EMAIL", "CONFLUENCE_API_TOKEN"
        )
        self.base_url = env["CONFLUENCE_BASE_URL"].rstrip("/")
        self.session = requests.Session()
        self.session.auth = (env["CONFLUENCE_EMAIL"], env["CONFLUENCE_API_TOKEN"])
        self.session.headers["Accept"] = "application/json"

    def _get(self, path, **params):
        resp = self.session.get(f"{self.base_url}{path}", params=params, timeout=30)
        if resp.status_code == 401:
            raise SystemExit("Confluence rejected the credentials (401). Check email and token.")
        if resp.status_code == 403:
            raise SystemExit("Confluence denied access (403). The token may lack permission.")
        resp.raise_for_status()
        return resp.json()

    def check_connection(self):
        """Return the display name of the authenticated user."""
        return self._get("/rest/api/user/current")["displayName"]

    def get_page(self, page_id):
        return self._get(f"/rest/api/content/{page_id}", expand=PAGE_EXPAND)

    def list_descendants(self, parent_id, batch=100):
        """Return (id, title) for every page under parent_id, at any depth."""
        pages, start = [], 0
        while True:
            data = self._get(
                f"/rest/api/content/{parent_id}/descendant/page", limit=batch, start=start
            )
            pages += [(r["id"], r["title"]) for r in data["results"]]
            if len(data["results"]) < batch:
                return pages
            start += batch

    def list_attachments(self, page_id):
        """Return (filename, download_path) for each file attached to the page."""
        files, start = [], 0
        while True:
            data = self._get(
                f"/rest/api/content/{page_id}/child/attachment", limit=100, start=start
            )
            files += [(r["title"], r["_links"]["download"]) for r in data["results"]]
            if len(data["results"]) < 100:
                return files
            start += 100

    def download(self, download_path, destination):
        """Save the file at a Confluence download path to the destination path."""
        resp = self.session.get(f"{self.base_url}{download_path}", timeout=60)
        resp.raise_for_status()
        destination.write_bytes(resp.content)

    def search_pages(self, text, limit=25):
        """Find pages whose title or body contains text. Returns (id, title, space) rows."""
        safe = text.replace("\\", "\\\\").replace('"', '\\"')
        cql = f'type = page AND (title ~ "{safe}" OR text ~ "{safe}")'
        data = self._get("/rest/api/content/search", cql=cql, limit=limit, expand="space")
        return [(r["id"], r["title"], r["space"]["key"]) for r in data["results"]]
