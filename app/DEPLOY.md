# Deploying the Insect Identifier

Before deploying, run it on your Mac and make sure you like the results:

    pip install -U -r requirements.txt
    python -m streamlit run app.py

## Memory (this decides which option works)
- BioCLIP 2 (default) holds a very large species-label table in RAM. Plan for 6+ GB.
- BioCLIP v1 (set env var BIOCLIP_MODEL=v1) is much lighter, but less accurate.
These are my estimates; check the logs if the app crashes.

## Option B: Streamlit Community Cloud (free, small memory limit)
1. Create a GitHub repo (e.g. insect-id) and upload: app.py, core.py, requirements.txt
   (test_core.py is optional).
2. Go to share.streamlit.io, sign in with GitHub, click "Create app" / "New app".
3. Pick the repo, branch main, main file path app.py.
4. Click "Advanced settings": choose Python 3.11 (or 3.12), and under Secrets add:
       BIOCLIP_MODEL = "v1"
   (BioCLIP 2 will very likely exceed the free memory limit.)
5. Deploy. The first start downloads the model and can take several minutes.
6. On your phone open the app URL, then Share -> Add to Home Screen.
If it shows "resource limits" / keeps restarting, it ran out of memory: use Option D.

## Option D: Oracle Cloud Always Free (permanent, enough RAM for BioCLIP 2)
1. Sign up at oracle.com/cloud/free (a credit card is needed for identity checks).
2. Create a compute instance:
   - Image: Ubuntu 22.04 (Canonical)
   - Shape: VM.Standard.A1.Flex (Ampere ARM), e.g. 4 OCPUs and 24 GB memory
     (Always Free allows up to that total). If you see "Out of capacity", try again
     later or another availability domain.
   - Add your SSH public key (or let Oracle generate one and download it).
3. Open port 8501: in the Oracle console go to your instance's subnet -> Security List
   -> Add Ingress Rule: Source CIDR 0.0.0.0/0, TCP, destination port 8501.
4. SSH in:  ssh -i path/to/key ubuntu@YOUR_PUBLIC_IP
5. On the server:
       sudo iptables -I INPUT -p tcp --dport 8501 -j ACCEPT
       sudo apt update && sudo apt install -y python3-venv python3-pip git
       git clone https://github.com/YOUR_USER/insect-id.git && cd insect-id
       python3 -m venv .venv && source .venv/bin/activate
       pip install -r requirements.txt
       python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
6. Open http://YOUR_PUBLIC_IP:8501 on your phone to test.
7. To keep it running after you close SSH, create /etc/systemd/system/insect.service:

       [Unit]
       Description=Insect ID
       After=network.target
       [Service]
       User=ubuntu
       WorkingDirectory=/home/ubuntu/insect-id
       ExecStart=/home/ubuntu/insect-id/.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
       Restart=always
       [Install]
       WantedBy=multi-user.target

   then:  sudo systemctl daemon-reload && sudo systemctl enable --now insect

Notes: the app is open to anyone who has the address. HTTPS (needed only for the in-app
camera widget, not for choosing/taking a photo through the upload button) can be added
later with Cloudflare Tunnel or a domain + Caddy.
