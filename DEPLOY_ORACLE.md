# Oracle Cloud Always Free Deployment Guide

This guide is specifically tailored for deploying the Enterprise Discord Management Platform on an Oracle Cloud Always Free tier instance (VM.Standard.E2.1.Micro - 1GB RAM, 1/8 OCPU).

Due to the limited resources (1GB RAM) on the Always Free tier, our installer automatically applies several optimizations.

## 1. Create the Instance

1.  Log in to Oracle Cloud Infrastructure (OCI).
2.  Go to **Compute** -> **Instances** -> **Create Instance**.
3.  **Image:** Select **Ubuntu 24.04** (or 22.04).
4.  **Shape:** Select `VM.Standard.E2.1.Micro` (Always Free eligible).
5.  **Networking:** Assign a Public IPv4 address.
6.  **SSH Keys:** Save the private key.

## 2. Configure VCN Firewall (Crucial)

Oracle Cloud blocks all incoming traffic by default at the network level. You MUST open ports 80 and 443.

1.  Go to **Networking** -> **Virtual Cloud Networks**.
2.  Click your VCN -> **Security Lists** -> **Default Security List**.
3.  Add an **Ingress Rule**:
    *   Source CIDR: `0.0.0.0/0`
    *   Destination Port Range: `80,443`
    *   Protocol: `TCP`

## 3. Connect to the Instance

```bash
ssh -i path/to/private_key ubuntu@<YOUR_PUBLIC_IP>
```

## 4. Run the One-Click Installer

The installer automatically detects the low RAM environment and configures swap space and database tuning.

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/discord-management-platform/main/install.sh | sudo bash
```

### What the Installer Optimizes for Oracle Cloud:
*   **Swap File:** Automatically creates a 2GB swap file to prevent Out of Memory (OOM) errors during npm builds or heavy usage.
*   **PostgreSQL Tuning:** Lowers `shared_buffers` to 128MB and `work_mem` to 4MB to conserve RAM.
*   **Redis Tuning:** Sets `maxmemory 128mb` with an LRU eviction policy.
*   **Sysctl:** Optimizes `vm.swappiness=10` and connection backlogs.
*   **Local Firewall (UFW):** Opens 80/443 locally to match the VCN rules.

## 5. Setup Domain & DNS

Point your domain (e.g., `bot.yourdomain.com`) to the Oracle Public IP using an A Record in your DNS provider (Cloudflare, Namecheap, etc.). Ensure this is done *before* running the installer if you select the SSL/Certbot option.

## Troubleshooting Memory Issues

If the bot crashes or the frontend fails to build, check the memory usage:
```bash
free -h
```
If swap is full, you may need to manually build the frontend locally and upload the `.next` folder, or increase the swap size to 4GB.
