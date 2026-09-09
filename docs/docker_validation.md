# Docker Validation

## Verified Runtime

The dashboard container was built and tested on 9 September 2026 using:

- Docker Desktop 4.89.0
- Docker Engine 29.7.2
- Linux image tag `au-credit-risk-analytics:v0.6.1`
- Image size 282,978,456 bytes
- Image digest `sha256:c78d10cfc3c7f44390b88b3628233c5b0dc234dc5478b205b1ec116157d53d42`

The container reached Docker health status `healthy`, returned `ok` from `/_stcore/health`, returned HTTP 200 from the dashboard root, and rendered the expected portfolio and model metrics without browser console errors.

## Commands

```bash
docker build -t au-credit-risk-analytics:v0.6.1 .
docker run --rm -p 8501:8501 au-credit-risk-analytics:v0.6.1
```

## Windows Custom Installations

When Docker Desktop is installed outside its standard location, the CLI and credential helper directory must both be available on `PATH`. For a session-only PowerShell adjustment:

```powershell
$env:PATH = "E:\bin\DockerDesktop\resources\bin;$env:PATH"
docker version
```

This does not modify the permanent user or system environment variables.
