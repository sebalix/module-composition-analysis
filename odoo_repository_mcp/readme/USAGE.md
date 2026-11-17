## Installation

Install this module together with the Odoo MCA modules collecting the data
(`odoo_repository` at least). The MCP submodules add their own tools to the
same server when installed.

## Expose the server to AI clients

- Enable the developer mode, then go to `AI > MCP Server`
- Open the `Odoo MCA MCP` server
- Click `Add Key` to generate an API key for a client: the key is displayed
  only once
- Configure the AI client with the `URL` shown on the server form and the
  generated key as `Bearer` token

## Security

- Tools run with the permissions of the user set on the API key: this user
  must belong to the `Odoo MCA User` group
  (`odoo_repository.group_odoo_repository_user`) to read the collected data
- Create one key per client; keys can be expired individually from the
  server form
- Every call is logged and can be audited in `AI > MCP Server Log`
