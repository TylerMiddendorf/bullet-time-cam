# Raspberry Pi SSH Access

This document records the non-secret connection details for development access to the current Raspberry Pi bench computer. The private key is intentionally stored outside this repository.

## Verified Connection

- SSH alias: `camerapi`
- Current hostname: `camerapi`
- Current IPv4 address: `10.0.0.136`
- SSH user: `username`
- SSH port: `22`
- Host key: ED25519 `SHA256:3xQxS6vIRxv/g08+mVYci64YNcIomXJVde/9Xr9PB5o`
- Verified on: July 10, 2026

The address is currently a LAN address rather than a documented static lease. If the router assigns a different address, update the `HostName` value in the local SSH config only after verifying the Pi's identity and host-key fingerprint.

## Local Key and Configuration

The dedicated key pair belongs to the local Windows account that runs Codex:

- Private key: `C:\Users\tyler\.ssh\camerapi_ed25519`
- Public key: `C:\Users\tyler\.ssh\camerapi_ed25519.pub`
- SSH configuration: `C:\Users\tyler\.ssh\config`
- Trusted host keys: `C:\Users\tyler\.ssh\known_hosts`

The private key is passwordless so local non-interactive agents can use it. It is dedicated to this Pi and must never be copied into the repository, committed, pasted into chat, or included in project archives. A `.gitignore` rule is not an adequate control for a private key.

The local `camerapi` SSH entry selects the address, user, dedicated identity, batch mode, and strict host-key checking. Connect from the same Windows account with:

```powershell
ssh camerapi
```

Verify that password fallback is not being used with:

```powershell
ssh -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no camerapi "hostname; id -un"
```

Expected output identifies host `camerapi` and user `username`.

## Agent Access Boundary

Local Codex tasks running under this Windows account can use `ssh camerapi`, subject to the task's network/sandbox approval. The key is not automatically available to cloud-hosted agents, other computers, other Windows accounts, or collaborators.

Key-based login authenticates the Linux user; it does not bypass Linux authorization. The account is a member of `sudo`, but SSH key access does not make `sudo` passwordless. Agents must stay within the user's requested scope and obtain approval before privileged or destructive changes.

Password authentication remains enabled as a recovery path. Change the previously exposed account password promptly. Disable password authentication only after key access and an independent recovery method have been verified.

## Recovery and Rotation

- If SSH reports a changed host key, stop and verify the Pi locally. Do not blindly remove the old key.
- To revoke this agent key, remove the `authorized_keys` line ending in `codex-camerapi-2026-07-10` on the Pi.
- To rotate the key, create a new dedicated pair, install and test it in a second session, then remove the old public key.
- Keep a local-console or other recovery path before tightening SSH authentication settings.
