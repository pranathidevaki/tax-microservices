# Tax Calculation Microservices — DevOps Lab Project (Weeks 1–9)

A tax calculator split into **3 microservices**. The code lives on **GitHub**. **Jenkins** builds and tests it on
every push. Each service runs in a **Docker** container, and **Kubernetes** runs and manages the containers.

```
 Browser ──► frontend (Nginx) ──/api/tax/*──► income-tax-service (Python/Flask)  ×2 pods
                              ──/api/gst/*──► gst-service (Node.js/Express)       ×2 pods

 git push ──► GitHub ──► Jenkins: checkout → docker build → unit tests → kubectl deploy ──► Kubernetes
```

| Service | Tech | Port | What it does |
|---|---|---|---|
| `income-tax-service` | Python, Flask | 5000 | Income tax FY 2026-27: new vs old regime, slab breakdown, 87A rebate, 4% cess |
| `gst-service` | Node.js, Express | 3000 | GST: CGST+SGST (same state) or IGST (other state), GST-inclusive or exclusive |
| `frontend` | HTML + Nginx | 80 | The web forms. Nginx also forwards `/api/...` calls to the right service |

```
tax-microservices/
├── frontend/             index.html (the forms), nginx.conf, Dockerfile
├── income-tax-service/   app.py, tax_logic.py, test_tax_logic.py, requirements.txt, Dockerfile
├── gst-service/          server.js, gst.js, gst.test.js, package.json, Dockerfile
├── docker-compose.yml    starts all 3 containers with one command
├── k8s/                  Kubernetes Deployment + Service for each microservice
└── Jenkinsfile           the CI/CD pipeline
```

> Commands below work in **PowerShell** (Windows) and **Terminal** (Mac/Linux). Run them from inside the
> `tax-microservices` folder unless a step says otherwise.

---

## Step 0 — Install the tools (skip what you already have)

1. **Git**: git-scm.com
2. **Docker Desktop**: docker.com/products/docker-desktop. Open it once and wait for "Engine running".
3. **Java 17 or 21** (Temurin from adoptium.net) and **jenkins.war** (jenkins.io/download → Generic Java package), saved in `C:\jenkins`.
4. **GitHub account**: github.com

Check that everything works:
```bash
git --version
docker --version
kubectl version --client
```
(`kubectl` comes with Docker Desktop.)

---

## Step 1 — Week 1: Look at the form (the frontend)
Open `frontend/index.html` in VS Code. It has two forms: income tax (income, deductions, a salaried checkbox)
and GST (amount, rate, inclusive and inter-state checkboxes). They use HTML validation (`type="number"`,
`min="0"`, `required`). JavaScript `fetch()` sends the form data as JSON to the backend services.
*(This is the week-1 "registration form" exercise, applied to this project.)*

## Step 2 — Week 2: Git basics, put the project under version control
```bash
cd tax-microservices
git init
git config user.name "Your Name"
git config user.email "you@example.com"
git status                 # every file shows as untracked
git add .
git commit -m "Initial commit: tax calculation microservices"
git log --oneline
```

## Step 3 — Week 2: Push to GitHub
1. GitHub → **New repository** → name: `tax-microservices` → **Public** → don't tick "Add README" → **Create**.
2. Then run:
```bash
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/tax-microservices.git
git push -u origin main
```
Refresh the GitHub page. All the files should be there.

## Step 4 — Week 3: Source code management (branch → change → pull request → merge)
```bash
git checkout -b feature/update-title
```
In `frontend/index.html`, change `<h1>Tax Calculation Microservices</h1>` to `<h1>Tax Calculator – <Your Name></h1>`. Then:
```bash
git diff                       # shows exactly what you changed
git add frontend/index.html
git commit -m "Update page title"
git push -u origin feature/update-title
```
On GitHub: **Compare & pull request** → **Create pull request** → **Merge pull request**. Then bring the merge back to your laptop:
```bash
git checkout main
git pull
git log --oneline --graph
```

## Step 5 — Week 6: Docker commands, one container at a time
```bash
docker build -t gst-service ./gst-service     # build an image from the Dockerfile
docker images                                 # list images
docker run -d -p 3000:3000 --name gst gst-service   # start a container in the background
docker ps                                     # list running containers
```
Open **http://localhost:3000/health** → `{"status":"UP", ...}`, and **http://localhost:3000/rates**.
```bash
docker logs gst                               # what the app printed
docker exec -it gst sh                        # go inside the container (type: ls, then exit)
docker stop gst                               # stop it
docker ps -a                                  # stopped containers are still listed
docker rm gst                                 # delete the container (the image stays)
```

## Step 6 — Week 7: Run the whole containerized app with Docker Compose
```bash
docker compose up --build
```
Open **http://localhost:8081**:
- Income ₹15,00,000 with ₹1,50,000 deductions → **New regime ₹97,500** vs Old ₹2,10,600 (new is cheaper)
- GST ₹1,000 @ 18% → CGST ₹90 + SGST ₹90 = ₹1,180. Tick inter-state → IGST ₹180.
- The two dots at the bottom turn green when both backend services are healthy.

Press `Ctrl+C`, then:
```bash
docker compose down
```

## Step 7 — Week 4: Start Jenkins as yourself
Run Jenkins from a terminal instead of as a Windows service. The service runs as a system account that can't use
your Docker Desktop or your Kubernetes settings. Open a **separate PowerShell window** and keep it open:
```bash
cd C:\jenkins
java -jar jenkins.war --httpPort=9090
```
Open **http://localhost:9090** → paste the password printed in that window → **Install suggested plugins** →
create your admin user → Save and Finish.

## Step 8 — Week 5: Create the CI pipeline in Jenkins
1. **New Item** → name `tax-pipeline` → **Pipeline** → OK.
2. Scroll to **Pipeline** → Definition: **Pipeline script from SCM** → SCM: **Git** →
   Repository URL: `https://github.com/<YOUR_USERNAME>/tax-microservices.git` → Branch: `*/main` →
   Script Path: `Jenkinsfile` → **Save**.
3. Click **Build Now**. Open the build → **Console Output** (or **Pipeline Overview**).
   Stages: **Checkout → Build Docker images → Unit tests** (12 Python + 6 Node tests, run in parallel inside the containers). It should finish green.

**Show continuous integration (the push triggers the build):**
the Jenkinsfile checks GitHub every 2 minutes (`pollSCM`). Edit any file, then `git commit` and `git push`.
Within about 2 minutes a new build starts by itself.

**Show a failing build:** in `income-tax-service/test_tax_logic.py` change `== 192_400` to `== 999`, then commit and push.
The **Unit tests** stage turns red. Change it back, commit and push, and the build goes green again.

## Step 9 — Week 8: Start Kubernetes and deploy by hand
1. Docker Desktop → ⚙ **Settings → Kubernetes → Enable Kubernetes**. If asked, choose **kubeadm** (it can use your
   local images). **Apply & restart**. Wait for "Kubernetes running".
2. Then run:
```bash
kubectl config use-context docker-desktop
kubectl get nodes                  # 1 node, Ready
docker compose build               # make sure the :latest images exist
kubectl apply -f k8s/
kubectl get pods                   # wait for 5 pods: Running, READY 1/1
kubectl get deployments,svc
```
3. Find the port: `kubectl get svc frontend` shows `NodePort` and `80:30090/TCP`, so 30090 is the port.
   Open **http://localhost:30090**. If it doesn't load, run this, keep it running, and open http://127.0.0.1:18082:
```bash
kubectl port-forward service/frontend 18082:80 --address 127.0.0.1
```

## Step 10 — Week 9: Let Jenkins automate the Kubernetes deployment
1. Jenkins → `tax-pipeline` → **Build with Parameters** → tick **DEPLOY_TO_K8S** → **Build**.
2. A 4th stage, **Deploy to Kubernetes**, now runs `kubectl apply`, switches every Deployment to this build's image
   tag (e.g. `gst-service:3`) and waits for the rolling update to finish.
3. Check the result:
```bash
kubectl get pods                                    # new pods with fresh ages
kubectl describe deployment gst-service | findstr Image     # Mac/Linux: grep Image  → shows :<build number>
kubectl rollout history deployment/frontend
```
4. End-to-end demo: change the `<h1>` title again, then commit and push. Run **Build with Parameters** with the box
   ticked. Refresh the browser and the new title is live, without any manual docker or kubectl commands.

## Step 11 — Kubernetes demos for the presentation
```bash
kubectl scale deployment gst-service --replicas=4    # scaling up
kubectl get pods -l app=gst-service
kubectl delete pod <copy-one-gst-pod-name>           # self-healing: a replacement starts immediately
kubectl get pods
kubectl logs deployment/income-tax-service           # logs
kubectl rollout undo deployment/frontend             # roll back to the previous version
```
Refresh the web page a few times. The footer shows the **pod name** that answered, and it changes because the
Service load-balances across the pods.

## Step 12 — Clean up
```bash
kubectl delete -f k8s/
docker compose down
```

---

## Troubleshooting
| Problem | Fix |
|---|---|
| Jenkins: `'docker' is not recognized` / `command not found` | Docker was started or installed after Jenkins. Restart Jenkins from a fresh PowerShell window (Step 7) |
| Jenkins: `kubectl ... connection refused` | Kubernetes was turned on after Jenkins started. Restart Jenkins (Step 7) |
| Pods stuck in `ErrImagePull` / `ImagePullBackOff` | Kubernetes isn't using Docker's local images. Choose **kubeadm** in Step 9, or run `docker compose build` again |
| `port is already allocated` | Something else is using that port. Stop the old container (`docker ps`, `docker stop <id>`) or change the left-hand port number |
| Page loads but the dots are red | The backend isn't ready yet. Wait 10 s, or check `docker compose logs` / `kubectl get pods` |

## Tax rules used (FY 2026-27, unchanged by Budget 2026)
- **New regime:** 0–4L nil · 4–8L 5% · 8–12L 10% · 12–16L 15% · 16–20L 20% · 20–24L 25% · >24L 30%. Standard deduction ₹75,000. 87A rebate: taxable income up to ₹12L is tax-free, with marginal relief just above ₹12L.
- **Old regime:** 0–2.5L nil · 2.5–5L 5% · 5–10L 20% · >10L 30%. Standard deduction ₹50,000 plus your deductions. 87A rebate up to ₹12,500 if taxable income ≤ ₹5L.
- 4% health & education cess. Surcharge (income above ₹50L) is not modelled.
- **GST 2.0** (from 22 Sep 2025): 0%, 5%, 18%, 40%, plus 3% (gold/jewellery) and 0.25% (rough diamonds).
