## Project Baobab Helm Chart
This directory contains the Helm chart which is automatically packaged on commit to the `main` branch and the artifacts published to `https://teamorea.github.io/project-baobab/`.

### Required Values

The following values must be provided when installing the chart:

- `secrets.SQLALCHEMY_DATABASE_URI`: database URL here in the format `postgresql://user:password@host:port/database`.
- `GHCR_auth_json`: this should be in the format '{"auths":{"ghcr.io":{"auth":"username:token | base64"}}}'.

Other values in the `values.yaml` file are optional and can be customized to taste.

Example usage:

```bash
helm install my-release project-baobab \
  --set secrets.SQLALCHEMY_DATABASE_URI=postgresql://user:password@host:port/database \
  --set GHCR_auth_json={"auths":{"ghcr.io":{"auth":"username:token | base64"}}}
```
An example deployment of this chart can be found at `kubernetes/project-baobab`.
  