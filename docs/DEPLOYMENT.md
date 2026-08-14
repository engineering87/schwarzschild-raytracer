# Deployment

The simulation is published to Azure Static Web Apps by
`.github/workflows/azure-static-web-apps.yml`, which runs on every push to
`main`. The workflow stages `index.html` and `staticwebapp.config.json` into a
`_site` directory and uploads only those, so the images, the offline renderer,
and the documentation stay in the repository without being served. The deployed
payload comes to under 100 kB.

Preview environments for pull requests are deliberately left unconfigured. A
single page gains little from them, and the reference renderer under `tools/`
already provides a way to inspect a change before it lands.

## Setting up a fresh Azure resource

Create the Static Web App. The important part is the deployment source: choose
**Other**, not GitHub. Choosing GitHub makes Azure commit a workflow of its own
into the repository, pointing at a secret whose name carries the generated
hostname as a suffix, and you end up with two pipelines deploying the same
artefact under different credentials.

```bash
az staticwebapp create \
  --name schwarzschild-raytracer \
  --resource-group <your-resource-group> \
  --location westeurope \
  --sku Free
```

The Free tier is offered in a limited set of regions, and `westeurope` is one of
them. Picking an unsupported region fails with an error that does not say so
clearly.

Read the deployment token:

```bash
az staticwebapp secrets list \
  --name schwarzschild-raytracer \
  --query "properties.apiKey" -o tsv
```

Store it under Settings, Secrets and variables, Actions, on the Secrets tab, as
a repository secret named exactly `AZURE_STATIC_WEB_APPS_API_TOKEN`. Then push
to `main`.

Read the hostname that Azure assigned, and update the live link in `README.md`
and the `url` field in `CITATION.cff`:

```bash
az staticwebapp show --name schwarzschild-raytracer \
  --query "defaultHostname" -o tsv
```

## Diagnosing a failed deployment

The first step of the workflow resolves the secret and reports whether it
arrived, printing its length and a truncated hash rather than the value itself.
The deploy action reports a missing token as an unknown exception from inside
its container, several steps after the real cause, so that check exists to name
the problem where it happens.

If the step reports an empty string, work through the list it prints. The usual
causes are a Static Web App that does not exist yet, a secret stored on the
Variables tab instead of the Secrets tab, a name that differs in case, or an
organization secret whose access has not been granted to this repository.

If a run fails while a different run succeeds, check whether a second workflow
is present:

```bash
grep -rn "AZURE_STATIC_WEB_APPS_API_TOKEN" .github/workflows/
```

A file named `azure-static-web-apps-<adjective>-<noun>-<hex>.yml` was generated
by Azure and should be removed. It can be told apart in the logs by the order of
the environment variables passed to Docker, since it forwards `repo_token` and
does not set `app_location` or `skip_app_build` explicitly.

Once the deployment succeeds, confirm that the configuration file was picked up:

```bash
curl -sI https://<hostname>/ | grep -i content-security-policy
```

## What staticwebapp.config.json does

It sets a ten minute cache lifetime with revalidation, a routing fallback that
sends everything to the simulation, and a content security policy that permits
only the inline script and the IBM Plex web font.

That policy is strict enough to break the page silently if the structure of
`index.html` changes. Moving the JavaScript into a separate file, or pulling in
a library from a content delivery network, will be blocked and the canvas will
stay black with the reason visible only in the browser console. Update the
policy in the same commit as any such change.
