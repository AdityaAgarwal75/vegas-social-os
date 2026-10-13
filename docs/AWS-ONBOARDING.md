# AWS → private dashboard → your accounts

This is an agent-executable installation recipe, not a promise that every ChatGPT host exposes every AWS action. Each user authorizes their own AWS connector. The setup agent must inspect its actual tools and permissions. Do not ask for AWS access keys in chat. Do not use the maintainer's instance, IP, OAuth app or Flow cookies.

## Starting request

Give a capable ChatGPT/Codex setup agent this repository URL and say:

> Install my independent Vegas Social OS in my AWS account. Read BOOTSTRAP.md and docs/AWS-ONBOARDING.md, inspect available tools, prepare a regional cost quote and deployment plan, and use deploy/aws/instance.json. After I approve the billable resources, provision, verify HTTPS and the private browser, then give me a one-use dashboard setup link. Keep secrets out of chat and public logs. I will complete Google/Meta sign-in and app approvals in the dashboard.

If a VPS already exists, reuse it with permission and an isolated service instead of buying another. No Render, Supabase or paid AI API is required by this edition. AWS, public IPv4, storage and Google Flow usage are separate costs.

## Agent workflow

1. Discover the authenticated AWS account, desired region, available EC2 types/quotas and connector actions. Recommend Ubuntu 24.04 **amd64/x86_64**, two vCPUs, **8 GiB RAM** and 40 GiB encrypted gp3 for multiple saved accounts with serialized active browser work. A 4 GiB `t3.medium` is an initial one-browser test option, not a multi-browser performance guarantee. The template permits `t3.medium`, `t3.large` and `m7i-flex.large`; verify availability/pricing. T3 uses **standard** CPU credits to avoid unlimited-credit surcharges, which may throttle sustained work.
2. Resolve the official Canonical Ubuntu 24.04 amd64 AMI in the selected region using AWS public SSM parameters, then verify architecture and AMI owner. Do not use an arbitrary Marketplace image or hardcoded AMI from another region. Resolve and review a specific 40-character repository commit for `SourceCommit`.
3. Price compute, encrypted gp3, **Elastic IP/public IPv4**, data transfer and backups using current regional AWS data. Show the concrete resources and get billable-resource approval before creating a stack. AWS credits/free tier are account-specific; never promise permanently free hosting.
4. Read `deploy/aws/instance.json`. It creates a dedicated VPC, public subnet, internet route, Web security group, SSM-only instance role/profile, EC2 and Elastic IP. Only **80/443** are inbound. SSH, browser/CDP/noVNC and SQLite ports are never public. IMDSv2 is required. No AWS admin permission is given to the instance.
5. Validate syntax/schema with cfn-lint, security with cfn-guard when available, and AWS `ValidateTemplate`/change-set checks through the connector. Create a CloudFormation change set with `CAPABILITY_IAM`; inspect it. A connector with read-only AWS permissions cannot deploy: report exact missing actions rather than claiming success.
6. Execute only the approved change set. Use a stable stack name and request token. After timeout, inspect the same operation rather than creating another stack. Wait for EC2 status checks, SSM online status and bootstrap completion. Stack completion alone does not prove app installation succeeded.
7. The Elastic IP stays stable across stop/start. For a custom hostname, use the user's authorized DNS tool to create its A record. Without one, the template derives `social.PUBLIC-IP-WITH-DASHES.sslip.io`; this external free DNS service and ACME certificate issuance are dependencies, not guarantees. Route outputs show the actual address and hostname, so the user need not work out the IP manually.
8. Use SSM Run Command (or the connected authorized execution tool) on the **new instance only** to inspect `/var/lib/vegas-social-os/bootstrap-complete`, systemd, local `/health`, HTTPS `/health`, and unauthenticated `/api/state` rejection. Inspect redacted cloud-init logs only if bootstrap fails. Ubuntu AMIs must include the SSM agent; if absent, install the official regional package via approved cloud-init changes, not by opening SSH publicly.
9. Test disposable signed-out Flow browser launch without spending credits. Do not copy the maintainer's profiles. Run tests. Confirm persistence after restarting the application's service; avoid rebooting an unrelated server.
10. Create a private one-use pairing URL with `scripts/new-setup-link.sh` **after checks**, via a private execution connector. The URL is secret and expires in ten minutes. Never put it in CloudFormation outputs, cloud-init, a public GitHub issue or a shared log. SSM command output is visible to AWS principals with command-read access: use only the user's private authorized account and return the link privately. Refresh an expired link rather than loosening authentication.
11. Give the dashboard link, pairing link and `/mcp` endpoint. Guide profile → provider app settings → account consent → read-only verification → channel brief. Every OAuth callback is displayed in Connections using this installation's actual hostname.
12. Create/install an optional private host plugin only if the user's tools support it; user installation consent remains host-controlled. Verify `doctor`, `connection_setup`, `account_list` and `automation_status`. If host scheduling exists, configure it to read `morning_queue`, research, save two concepts using the task ID, and call `brief_complete`. Verify a real trigger; a queue alone is not autonomous creative execution.

## Permission boundaries

The setup connector needs the CloudFormation lifecycle/read actions, EC2/VPC/network/address/volume operations required by this template, creation and attachment of this stack's IAM role/profile, narrowly scoped `iam:PassRole` for that role, and SSM command/status actions on the target instance. Use its AWS service-authorization metadata to produce a scoped policy; do not recommend administrator credentials or wildcard PassRole. The template creates `AmazonSSMManagedInstanceCore` as the instance's baseline; it does **not** allow that VPS to create other EC2 instances or administer the account.

Social app approvals are independent of AWS permissions. A user's existing ChatGPT Google Drive/GitHub/Google sign-in does not create a YouTube OAuth client or authorize Meta Pages on the VPS.

## Failure recovery and ownership

Bootstrap is pinned to a reviewed commit. For a failed install, inspect the same instance and rerun the installer after correcting its cause. Never create another instance as an automatic retry. Keep a manifest of stack/instance/IP/volume IDs and verified source commit in the user's private workspace.

The root volume has `DeleteOnTermination=false` to preserve private accounts/media. **Deleting a stack or terminating the instance leaves a billable root volume**; it is not a backup, and removing the Elastic IP breaks callbacks. Before any deletion/replacement, back up and test restore; get separate destructive authorization. Offboarding includes explicit encrypted-volume cleanup and Elastic IP release only when the owner confirms data is no longer needed. Changing AMI/root disk in CloudFormation may replace an instance: do not use infrastructure replacement as an application update.

Fresh-account AWS creation has not been executed as part of the founder's existing-server update. Treat this template as validated source until a new AWS installation completes the checks above.
