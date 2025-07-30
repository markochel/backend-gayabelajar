from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.routers import admin, auth, siswa, guru, soal

app = FastAPI()

# Tambahkan semua router
app.include_router(auth.router)
app.include_router(siswa.router)
app.include_router(guru.router)
app.include_router(soal.router)
app.include_router(admin.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # untuk development lokal
        "https://cekgayabelajar.vercel.app",  # untuk produksi (Vercel)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
