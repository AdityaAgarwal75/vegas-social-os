"""Provider-independent instructions for Meta Social Technologies MCP assisted onboarding.

This server does not impersonate the user's ChatGPT/IDE Meta MCP session.
The agent must independently discover and call devtools_* tools, with explicit
owner OAuth and per-app grants. Unknown and unverified are not "approved".
"""
from .config import Config

MCP_URL = "https://mcp.facebook.com/devtools"
DOCS_URL = "https://developers.facebook.com/documentation/mcp/devtools-mcp"
READ_ACTIONS = {
    "devtools_app_list": ["list"],
    "devtools_app": ["basic_settings", "advanced_settings", "security", "restrictions", "data_protection_officer"],
    "devtools_app_review": ["status", "history", "privileges", "requirements"],
    "devtools_compliance": ["status"],
    "devtools_api_usage": ["rate_limits", "call_volume", "deprecations"],
    "devtools_webhook_list": ["list_topics", "list_subscriptions"],
    "devtools_discovery": ["search_docs"],
    "devtools_api_changelog": ["list_products", "get_changelog_url", "get_rss_url"],
}
WRITE_ACTIONS = {
    "devtools_webhook_manage": ["subscribe", "unsubscribe", "update_fields"],
    "devtools_webhook_test": ["test_send"],
}
COMING_SOON = [
    "devtools_app_create", "devtools_app_use_cases", "devtools_app_use_cases_manage",
    "devtools_business_list", "devtools_business_create", "devtools_app_business_manage",
]


def guidance(engine):
    """Give a ChatGPT agent the exact user-owned onboarding dependencies.

    This is a *local guide*, not proof the external Meta MCP is connected,
    permissions approved, or any developer-side changes executed.
    """
    config = Config(engine.store, engine.base)
    facebook = config.public("facebook")
    instagram = config.public("instagram")
    return {
        "title": "Meta MCP assisted developer-app setup",
        "mcp_server": MCP_URL,
        "documentation_url": DOCS_URL,
        "connection_type": "OAuth in the owner's ChatGPT/IDE client; not a VPS server-to-server token",
        "meta_mcp_connection": "unverified_from_vps",
        "beta_access": "Account/host dependent. Do not require Meta MCP to use basic Vegas Social OS.",
        "facebook": {
            "app_id": facebook["client_id"],
            "credentials_configured": facebook["configured"],
            "secret_present": facebook["secret_present"],
            "graph_version": facebook["graph_version"],
            "oauth_callback_urls": facebook["callbacks"],
            "requested_scopes": facebook["permissions"],
            "oauth_grant": "unverified_by_this_guide",
        },
        "instagram": {
            "app_id": instagram["client_id"],
            "credentials_configured": instagram["configured"],
            "oauth_callback_urls": instagram["callbacks"],
            "requested_scopes": instagram["permissions"],
            "oauth_grant": "unverified_by_this_guide",
        },
        "supported_read_tools": READ_ACTIONS,
        "supported_manage_tools": WRITE_ACTIONS,
        "upcoming_unavailable_tools": COMING_SOON,
        "action_sequence": [
            "Owner connects Meta Social Technologies MCP over OAuth in the ChatGPT/IDE client and selects the correct apps.",
            "Agent calls devtools_app_list to determine actual granted apps and read/manage access; never infer from the Meta dashboard alone.",
            "Agent inspects devtools_app advanced_settings plus devtools_app_review privileges, status and requirements for the exact app ID.",
            "Agent compares exact OAuth redirect URIs to this installation's callback URL and reports mismatches; Meta MCP currently cannot update redirect URIs.",
            "Agent checks compliance, API health and existing webhooks before suggesting changes.",
            "Agent requests confirmation before modifying any webhook subscription, including tests that trigger real callback traffic.",
            "Owner enters App ID/Secret in the PRIVATE installation dashboard, never ChatGPT or GitHub; owner completes official Facebook/Instagram OAuth consent.",
            "Agent rechecks Social OS connection setup and confirmed provider identities; meta_mcp_manage scope does not grant Instagram content permissions.",
        ],
        "human_actions": [
            "Meta developer OAuth app selection and consent",
            "Set or correct OAuth redirect URLs and provider app secrets in their respective private dashboards",
            "Grant required Page/professional account login consent",
            "Complete App Review and any required business verification",
            "Review and approve destructive social-provider writes",
        ],
        "future_automation_policy": "Only call app-creation, use-case or business-link tools if dynamically discovered on the connected Meta MCP client; require owner confirmation and verify outputs. Never promise them today.",
        "manual_fallback": "Continue with provider console and encrypted dashboard setup when Meta MCP is absent, unavailable or not granted.",
    }
