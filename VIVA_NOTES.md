# Viva / Presentation Notes

## 1. 30-second pitch
"I built a Tax Calculation application as **microservices**: an income-tax service in Python, a GST service in
Node.js, and an Nginx frontend that sends each request to the right service. The code is version-controlled with
**Git** and hosted on **GitHub**. Each service is packaged as a **Docker** image. **Jenkins** watches the GitHub repo:
on every new commit it builds the images and runs the unit tests. If they pass, it deploys the new images to
**Kubernetes**, which runs 2 copies of each backend and load-balances between them. It also restarts crashed
containers and updates the app with zero downtime."

## 2. What each tool does
| Tool | Role in this project | Why use it |
|---|---|---|
| **Git** | tracks every change to the code | history, branches, undo, teamwork |
| **GitHub** | remote copy of the repo; Jenkins pulls from it | central source of truth, pull requests / code review |
| **Jenkins** | CI/CD server that runs the `Jenkinsfile` | automates build → test → deploy on every commit |
| **Jenkinsfile** | the pipeline written as code, stored in the repo | the pipeline is versioned and reviewed like any other code |
| **Docker** | packages each service plus its runtime into an image | "works on my machine" → works everywhere |
| **Dockerfile** | the recipe for building an image | builds are reproducible |
| **Docker Compose** | starts several containers together on one machine | one command runs the whole app locally |
| **Kubernetes** | runs containers and keeps them running: scaling, self-healing, rolling updates, load balancing | production-grade container management |
| **Pod** | the smallest K8s unit, wraps one container | — |
| **Deployment** | "keep N pods of this image running" | self-healing + rolling updates |
| **Service** | a stable name + load balancer in front of the pods | pods change IP when they restart; the Service name doesn't |
| **kubectl** | command line tool for talking to Kubernetes | — |
| **Nginx** | serves the HTML and forwards `/api/tax` and `/api/gst` to the services (reverse proxy) | the browser only needs one address |
| **pytest / node --test** | unit tests that Jenkins runs | broken code never gets deployed |

## 3. The Jenkins pipeline, stage by stage
1. **Trigger**: `pollSCM('H/2 * * * *')` checks GitHub every ~2 minutes and builds if there's a new commit.
2. **Checkout**: clones the latest code from GitHub.
3. **Build Docker images**: builds 3 images, each tagged with the Jenkins build number (`gst-service:7`) and `latest`.
4. **Unit tests**: runs the Python and Node tests **in parallel**, *inside* the freshly built images. If one
   fails, the pipeline stops and nothing gets deployed. This is the **quality gate**.
5. **Deploy to Kubernetes**: `kubectl apply -f k8s/`, then `kubectl set image ...:<build number>`. Kubernetes does a
   **rolling update** and `rollout status` waits until it has finished.

Why tag with the build number? Each build is a separate image, so you can always tell which version is running,
and rolling back is just going back to the previous number (`kubectl rollout undo`).

## 4. CI vs CD
- **Continuous Integration**: every commit is automatically built and tested (stages 1–4).
- **Continuous Delivery**: every passing build produces a ready-to-ship artifact (the Docker images).
- **Continuous Deployment**: every passing build is deployed automatically (stage 5).

## 5. Likely questions
**Why microservices instead of one app?** Each part can use the best language, and can be deployed, scaled and
fixed on its own. If GST traffic spikes, I scale only `gst-service`. The trade-off is more moving parts and network calls between services.

**How does the frontend find the backends?** By name. Nginx forwards to `http://income-tax-service:5000`. Docker
Compose has its own DNS that resolves service names, and in Kubernetes the **Service** named `income-tax-service`
gets a DNS entry.

**Image vs container?** An image is a read-only template (like a class). A container is a running instance of it (like an object).

**Why copy `requirements.txt` before the source code in the Dockerfile?** Layer caching. Dependencies are only
reinstalled when that file changes, so rebuilding takes seconds.

**Why Gunicorn instead of `flask run`?** Flask's built-in server is only for development. Gunicorn is a production server that runs multiple worker processes.

**Why run as a non-root user in the container?** If someone breaks into the app, they don't get root.

**Readiness vs liveness probe?** Readiness asks "can I receive traffic yet?"; until it passes, the pod gets no
requests. Liveness asks "am I still alive?"; if it fails, Kubernetes restarts the container.

**What happens if a pod crashes?** The Deployment sees 1 pod running when 2 are wanted, and starts a new one. Demo it with `kubectl delete pod`.

**ClusterIP vs LoadBalancer?** ClusterIP is reachable only inside the cluster, which is all the backends need.
LoadBalancer is reachable from outside (the frontend). On Docker Desktop that means localhost; on a cloud provider it's a public load balancer.

**Rolling update?** Kubernetes starts the new pods and only removes the old ones once the new ones are ready, so there is no downtime.

**Docker Compose vs Kubernetes?** Compose runs containers on one machine and is good for development. Kubernetes
runs them across many machines and adds scaling, self-healing, rolling updates and load balancing.

**Why did a pushed commit build without me clicking anything?** `pollSCM` in the Jenkinsfile. A GitHub webhook
would be instant, but GitHub can't reach `localhost`, so polling is the right choice for a local Jenkins.

## 6. Syllabus mapping
| Week | Topic | In this project |
|---|---|---|
| 1 | Simple form | `frontend/index.html`: income tax and GST forms with validation |
| 2 | Git & GitHub commands | Steps 2–3: init, add, commit, log, remote, push |
| 3 | Source code management on GitHub | Step 4: branch, diff, push, pull request, merge, pull |
| 4 | Jenkins setup | Step 7: Jenkins with Docker access, plugins |
| 5 | CI with Jenkins | Step 8: `Jenkinsfile`, automatic build on push, failing-test demo |
| 6 | Docker commands | Step 5: build, images, run, ps, logs, exec, stop, rm |
| 7 | Containerized application | 3 Dockerfiles + `docker-compose.yml` (Step 6) |
| 8 | Kubernetes + Docker | `k8s/*.yaml`, `kubectl apply` (Step 9) |
| 9 | Automate running the app with Kubernetes | Jenkins "Deploy to Kubernetes" stage (Step 10) + scaling and self-healing demos (Step 11) |
