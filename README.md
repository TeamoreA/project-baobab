## Domain Lookup API
This is an API that helps discover domains. The full Swagger API documentation can be found at `https://<my domain here>/apidocs`

### Running the app locally
- Copy the contents of `.env.example` file to `.env` file and ensure you replace all placeholders accordingly.
- The app can be run locally using docker-compose with this command: `docker-compose up -d --build`
- Visit `http://localhost:3000/apidocs/` on your browser to discover all endpoints.

### Deployment to Kubernetes
This app has been deployed to Kubernetes using a helm chart. Building the docker image and packaging the helm chart is automatically done on commit to the `main` branch by GitHub Actions found at `.github/workflows/build-and-deploy.yaml`.

The compiled helm chart is found at `charts/project-baobab` and an example of deploying this Helm chart can be found here `kubernetes/project-baobab`.

_Please find detailed steps on deploying the helm chart here `charts/project-baobab/README.md`_
