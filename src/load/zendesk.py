"""Minimal Zendesk Help Center client (create articles only)."""
import requests

from src import config


class ZendeskClient:
    def __init__(self):
        env = config.require(
            "ZENDESK_SUBDOMAIN", "ZENDESK_EMAIL", "ZENDESK_API_TOKEN",
            "ZENDESK_SECTION_ID", "ZENDESK_PERMISSION_GROUP_ID",
        )
        self.base_url = f"https://{env['ZENDESK_SUBDOMAIN']}.zendesk.com"
        self.section_id = env["ZENDESK_SECTION_ID"]
        self.permission_group_id = int(env["ZENDESK_PERMISSION_GROUP_ID"])
        self.session = requests.Session()
        self.session.auth = (f"{env['ZENDESK_EMAIL']}/token", env["ZENDESK_API_TOKEN"])
        self.session.headers["Accept"] = "application/json"

    def create_article(self, article):
        """POST one article (the dict built by build_payload) and return the new article's id."""
        resp = self.session.post(
            f"{self.base_url}/api/v2/help_center/sections/{self.section_id}/articles",
            json={"article": article},
            timeout=30,
        )
        if resp.status_code == 401:
            raise SystemExit("Zendesk rejected the credentials (401). Check email and token.")
        if resp.status_code == 403:
            raise SystemExit("Zendesk denied access (403). The user may lack Guide permissions.")
        resp.raise_for_status()
        return resp.json()["article"]["id"]
