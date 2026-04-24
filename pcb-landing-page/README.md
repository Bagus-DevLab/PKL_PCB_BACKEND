# PCB Smart Kandang - Frontend

Landing page + Admin dashboard untuk platform IoT Smart Kandang.

Bagian dari monorepo [PKL_PCB_BACKEND](https://github.com/Bagus-DevLab/PKL_PCB_BACKEND).

## Tech Stack

- React 19 + Vite
- Tailwind CSS v4 + shadcn/ui
- Framer Motion (animasi)
- Recharts (chart dashboard)
- Firebase Web SDK (admin auth)
- Axios (API client)

## Development

```bash
cp .env.example .env
# Edit .env dengan Firebase config

npm install
npm run dev
```

Frontend dev server berjalan di `http://localhost:5173`.
Backend harus running di `http://localhost:8001` (via Docker).

## Build

```bash
npm run build
```

Output di `dist/`. Di production, build dilakukan otomatis oleh Dockerfile multi-stage di root project.

## Halaman

| Route | Deskripsi |
|-------|-----------|
| `/` | Landing page (publik) |
| `/admin/login` | Login admin (Firebase email/password) |
| `/admin/dashboard` | Dashboard overview (admin only) |
| `/admin/users` | Kelola user + role (admin only) |
| `/admin/devices` | Register + unclaimed devices (admin only) |
