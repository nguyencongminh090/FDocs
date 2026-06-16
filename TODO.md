# FDocs — TODO

## Deploy to Production

- [ ] Tạo SSH key pair cho deploy: `ssh-keygen -t ed25519 -C "fdocs-deploy" -f ~/.ssh/fdocs_deploy`
- [ ] Copy public key lên server: `echo "<public_key>" >> ~/.ssh/authorized_keys`
- [ ] Thêm secret `DEPLOY_HOST` vào GitHub repo (Settings → Secrets and variables → Actions)
- [ ] Thêm secret `DEPLOY_USER` vào GitHub repo
- [ ] Thêm secret `DEPLOY_SSH_KEY` vào GitHub repo (nội dung file `~/.ssh/fdocs_deploy`)
- [ ] Copy file `.env` lên server tại `~/fdocs/.env` với giá trị production thật

## Features

- [ ] **SSE Progress cho Upload**: Đổi `POST /api/documents` sang async job pattern (trả `202 + job_id` ngay), thêm `GET /api/upload/{job_id}/progress` SSE stream phát sự kiện `{stage, progress, total}`, frontend kết nối SSE và hiển thị progress bar realtime trong lúc embedding. Loại bỏ hoàn toàn nguy cơ 504 timeout.
