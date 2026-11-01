# Simple RAG — Document Workspace

Aplikasi Retrieval-Augmented Generation (RAG) untuk mengunggah PDF, mengajukan pertanyaan berdasarkan dokumen, dan membuat brief topik dengan referensi sumber. Backend menggunakan FastAPI, embedding lokal dari Sentence Transformers, Qdrant lokal untuk penyimpanan vektor, serta Groq untuk menghasilkan jawaban.

Website disajikan langsung oleh FastAPI. Frontend menggunakan HTML, CSS, dan JavaScript tanpa proses build, dengan desain **Material 3 Sky Night** dari [DESIGN-SKYNIGHT-SUBTLE.md](DESIGN-SKYNIGHT-SUBTLE.md).

## Daftar isi

- [Fitur](#fitur)
- [Teknologi](#teknologi)
- [Persiapan](#persiapan)
- [Instalasi dan menjalankan aplikasi](#instalasi-dan-menjalankan-aplikasi)
- [Konfigurasi](#konfigurasi)
- [Penggunaan website](#penggunaan-website)
- [Format Markdown jawaban](#format-markdown-jawaban)
- [Cara kerja RAG](#cara-kerja-rag)
- [Dokumentasi API](#dokumentasi-api)
- [Struktur proyek](#struktur-proyek)
- [Penyimpanan dan siklus data](#penyimpanan-dan-siklus-data)
- [Kustomisasi](#kustomisasi)
- [Batasan aplikasi](#batasan-aplikasi)
- [Pemecahan masalah](#pemecahan-masalah)

## Fitur

- Unggah satu PDF melalui pemilih file atau drag-and-drop.
- Ekstraksi teks per halaman dan pemecahan menjadi potongan berbasis token.
- Penyimpanan embedding dan metadata dokumen secara lokal.
- Pertanyaan dengan jawaban berdasarkan konteks yang ditemukan di knowledge base.
- Brief topik dengan struktur Summary, Key Points, dan Source References.
- Referensi nama dokumen dan nomor halaman pada jawaban maupun brief.
- Renderer Markdown untuk heading, bold, italic, daftar, tabel, kutipan, kode, dan format lainnya.
- Tombol Copy untuk menyalin respons asli beserta sintaks Markdown-nya.
- Daftar dokumen yang diunggah dalam sesi tab browser.
- Indikator koneksi API, status pemrosesan, dan pesan kegagalan.
- Layout responsif dengan palet navy, aksen biru langit, dan font sesuai spesifikasi desain.
- Dokumentasi API interaktif bawaan FastAPI.

## Teknologi

| Komponen | Implementasi |
| --- | --- |
| Web server dan API | FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript native |
| Parser Markdown | Marked 18.1.1, file lokal |
| Sanitasi HTML | DOMPurify 3.4.17, file lokal |
| Ekstraksi PDF | PyMuPDF |
| Pemecahan teks | LangChain RecursiveCharacterTextSplitter dengan tokenizer Hugging Face |
| Embedding | Sentence Transformers |
| Model embedding | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Database vektor | Qdrant Client dalam mode penyimpanan lokal |
| Penyedia LLM | Groq melalui `AsyncGroq` |
| Konfigurasi environment | python-dotenv |

## Persiapan

- Python dengan dukungan dependensi di [requirements.txt](requirements.txt). Python 3.11 atau 3.12 dapat dijadikan pilihan awal untuk environment machine learning; versi Python lain bergantung pada dukungan paket yang dipasang.
- API key Groq yang memiliki akses ke model yang dikonfigurasi.
- Koneksi internet untuk instalasi paket, pengunduhan model/tokenizer saat belum tersedia di cache, dan permintaan ke Groq.
- Ruang penyimpanan untuk paket Python, cache model, PDF, dan database Qdrant.

Tidak diperlukan Node.js, npm, atau server Qdrant terpisah untuk konfigurasi saat ini.

## Instalasi dan menjalankan aplikasi

Jalankan perintah dari direktori proyek yang berisi `main.py`.

### Windows / PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Jika `.env` sudah ada, gunakan file tersebut; jangan menimpanya saat mengulang instalasi. Isi API key melalui editor:

```dotenv
GROQ_API_KEY=isi_api_key_groq_anda
GROQ_MODEL=openai/gpt-oss-120b
```

Jalankan server:

```powershell
python -m uvicorn main:app --reload
```

Jika aktivasi virtual environment diblokir oleh pengaturan PowerShell, panggil interpreter secara langsung:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env dan isi GROQ_API_KEY sebelum menjalankan server.
python -m uvicorn main:app --reload
```

### Alamat aplikasi

| Halaman | Alamat default |
| --- | --- |
| Website | http://127.0.0.1:8000/ |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| OpenAPI JSON | http://127.0.0.1:8000/openapi.json |
| Health | http://127.0.0.1:8000/health |

Pada startup pertama, aplikasi memuat model embedding dan tokenizer; proses ini dapat memerlukan pengunduhan sebelum server siap. Untuk mengganti port, tambahkan `--port 8001`. Frontend menggunakan endpoint relatif sehingga otomatis mengikuti host dan port FastAPI.

Untuk menjalankan tanpa pemantauan perubahan kode:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Gunakan satu worker dengan Qdrant lokal karena direktori database dikunci oleh proses yang membukanya.

## Konfigurasi

### Environment variables

Salin [.env.example](.env.example) ke `.env`. File `.env` dimuat oleh `config.py` dan sudah masuk `.gitignore`.

| Nama | Wajib | Nilai / kegunaan |
| --- | --- | --- |
| `GROQ_API_KEY` | Ya | API key yang digunakan SDK Groq pada backend |
| `GROQ_MODEL` | Tidak | Model Groq; default kode saat ini adalah `openai/gpt-oss-120b` |

Nama model default mengikuti konfigurasi proyek. Akses dan ketersediaan model bergantung pada akun Groq; ganti `GROQ_MODEL` dengan model yang tersedia untuk akun Anda bila diperlukan.

API key tidak dikirim ke browser. Permintaan generasi dilakukan oleh backend. Teks konteks yang ditemukan dari dokumen dan pertanyaan/topik dikirim ke Groq untuk menghasilkan respons.

### Parameter di `config.py`

Parameter berikut diatur dalam kode, bukan melalui environment variable:

| Parameter | Nilai saat ini | Fungsi |
| --- | --- | --- |
| `UPLOAD_DIR` | `data/uploads/` | Lokasi PDF yang diunggah |
| `QDRANT_PATH` | `qdrant_data/` | Database vektor lokal |
| `COLLECTION_NAME` | `rag_documents` | Nama koleksi Qdrant |
| `EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Model embedding dan tokenizer |
| `TOP_K` | `4` | Jumlah potongan yang diambil untuk pertanyaan |
| `BRIEF_TOP_K` | `6` | Jumlah potongan yang diambil untuk brief |
| `CHUNK_SIZE` | `100` | Target ukuran maksimal potongan berdasarkan tokenizer |
| `CHUNK_OVERLAP` | `20` | Tumpang tindih token antar potongan |

`llm.py` mengatur temperature generasi ke `0.2`.

Jika model embedding diganti, gunakan koleksi/database yang sesuai dan ingest ulang dokumen. Vektor dari model berbeda tidak semestinya dicampur, bahkan bila dimensinya sama.

## Penggunaan website

### Mengunggah PDF

1. Pilih PDF melalui **browse files** atau seret file ke area **Drop a PDF here**.
2. Klik **Upload document**.
3. Tunggu proses pembacaan halaman, chunking, embedding, dan penyimpanan.
4. Setelah berhasil, dokumen muncul di **Uploaded this session**, beserta jumlah halaman terbaca dan potongan tersimpan.

Gunakan PDF yang memiliki teks yang dapat diseleksi. PDF scan tanpa lapisan teks memerlukan OCR di luar aplikasi ini.

### Mengajukan pertanyaan

1. Pilih tab **Ask a question**.
2. Masukkan pertanyaan yang spesifik, misalnya `Apa tiga rekomendasi utama dalam laporan ini?`.
3. Klik **Ask question**, atau tekan `Ctrl+Enter` / `Cmd+Enter`.
4. Baca respons di **Your answer** dan referensi di **Source references**.

Pertanyaan menelusuri seluruh knowledge base, termasuk dokumen dari sesi sebelumnya. Tidak perlu mengunggah ulang dokumen hanya karena daftar sesi browser kosong.

### Membuat brief

1. Pilih tab **Create a brief**.
2. Masukkan topik, misalnya `Risiko operasional dan langkah mitigasi`.
3. Klik **Create brief**, atau tekan `Ctrl+Enter` / `Cmd+Enter`.
4. Respons ditampilkan pada **Your brief** dengan referensi sumber.

Respons terakhir pada masing-masing tab tetap tersedia selama halaman terbuka. Respons sebelumnya dipertahankan jika permintaan berikutnya gagal. Riwayat percakapan tidak disimpan.

### Status API

Indikator header meminta `/health` ketika halaman dibuka. Tombol refresh memeriksa ulang koneksi. **API online** berarti endpoint health merespons; indikator ini tidak memverifikasi keberhasilan generasi Groq atau kualitas isi knowledge base.

## Format Markdown jawaban

Jawaban dan brief diproses sebagai Markdown dengan GitHub Flavored Markdown (GFM) menggunakan [Marked](https://marked.js.org/). HTML hasil parsing disaring oleh [DOMPurify](https://github.com/cure53/DOMPurify) sebelum ditampilkan.

Format yang didukung:

- Heading `#` sampai `######`.
- **Bold**, *italic*, ~~strikethrough~~, dan kombinasi penekanan.
- Daftar bernomor, bullet, daftar bertingkat, dan task list.
- Tabel dengan heading kolom dan alignment.
- Kutipan / blockquote dan garis pemisah.
- Inline code dan blok kode berpagar, termasuk penanda bahasa.
- Tautan, gambar, serta HTML terbatas seperti `<details>`, `<summary>`, `<sup>`, dan `<sub>`.
- Pergantian baris biasa ditampilkan sebagai line break.

Contoh output LLM yang dapat dirender:

````markdown
## Ringkasan

Temuan **utama** adalah peningkatan efisiensi dengan beberapa *catatan*.

| Aspek | Temuan | Prioritas |
| :--- | :--- | :---: |
| Proses | Waktu pengerjaan turun | Tinggi |
| Risiko | Perlu pemantauan berkala | Sedang |

### Tindak lanjut

1. Tinjau rekomendasi.
2. Tetapkan penanggung jawab.

- [x] Identifikasi masalah
- [ ] Susun rencana

> Kesimpulan harus tetap merujuk pada dokumen sumber.

Gunakan `TOP_K` untuk mengatur jumlah potongan konteks.

```python
print("Contoh blok kode")
```
````

Tabel lebar dan blok kode memiliki scroll horizontal. Area tabel dapat difokuskan dengan keyboard. Tautan dibuka di tab baru. Checkbox task list ditampilkan sebagai status, bukan kontrol yang bisa diedit.

Tombol **Copy** menyalin respons asli, sehingga sintaks Markdown tetap bisa ditempel ke editor lain. Jika library lokal tidak termuat, respons ditampilkan sebagai teks biasa.

Renderer tidak menjalankan script, CSS arbitrer, iframe, atau event handler dari output LLM. Rumus LaTeX, diagram Mermaid, dan syntax highlighting berwarna belum memiliki renderer khusus; blok kode tetap tampil dengan font monospace. Pemformatan mengikuti isi yang dihasilkan LLM—renderer tidak otomatis mengubah paragraf menjadi tabel.

Library Markdown disimpan pada `static/vendor/`, sehingga rendering tidak memerlukan CDN saat runtime. Font tetap menggunakan Google Fonts dengan fallback sans-serif/monospace jika tidak tersedia.

## Cara kerja RAG

### Pipeline ingestion

```text
PDF
  → ekstraksi teks per halaman (PyMuPDF)
  → pemecahan teks berbasis tokenizer
  → embedding lokal (Sentence Transformers)
  → penyimpanan vektor dan metadata di Qdrant
```

Setiap potongan menyimpan teks, nama sumber, nomor halaman asli PDF, dan indeks potongan dalam halaman. Halaman tanpa teks dilewati. Karena itu, `pages_read` menghitung halaman yang memiliki teks, bukan selalu total halaman PDF.

### Pipeline pertanyaan / brief

```text
Pertanyaan atau topik
  → embedding query
  → pencarian similarity di Qdrant
  → penggabungan potongan sebagai konteks
  → pengiriman system prompt + konteks ke Groq
  → respons teks + metadata sumber
  → rendering Markdown di browser
```

Pencarian menggunakan cosine similarity. Pertanyaan mengambil maksimal `TOP_K` potongan, sedangkan brief mengambil maksimal `BRIEF_TOP_K` potongan. Referensi sumber dideduplikasi berdasarkan pasangan nama dokumen dan halaman.

`score` adalah skor kemiripan hasil pencarian, bukan persentase keyakinan LLM. Daftar `sources` menunjukkan halaman yang masuk ke konteks; daftar ini tidak menjamin setiap klaim jawaban memiliki kutipan individual.

## Dokumentasi API

Contoh respons di bawah bersifat ilustratif. Isi jawaban, jumlah potongan, dan skor akan mengikuti dokumen dan hasil model.

### Ringkasan route

| Method | Route | Fungsi |
| --- | --- | --- |
| `GET` | `/` | Halaman website |
| `GET` | `/static/{path}` | Asset frontend dan library lokal |
| `GET` | `/health` | Status dasar API |
| `POST` | `/ingest` | Unggah dan indeks PDF |
| `POST` | `/ask` | Pertanyaan berbasis dokumen |
| `POST` | `/brief` | Brief berdasarkan topik |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | Dokumentasi ReDoc |
| `GET` | `/openapi.json` | Skema OpenAPI |

### `GET /health`

```json
{
  "status": "OK"
}
```

### `POST /ingest`

Kirim `multipart/form-data` dengan field `file` berisi satu PDF. Jangan menggunakan JSON untuk endpoint ini.

```bash
curl -X POST http://127.0.0.1:8000/ingest -F "file=@laporan.pdf"
```

Pada Windows PowerShell, gunakan `curl.exe` untuk contoh multipart di atas.

Contoh respons:

```json
{
  "source": "laporan.pdf",
  "pages_read": 12,
  "chunks_stored": 84
}
```

| Field | Arti |
| --- | --- |
| `source` | Nama file yang dipakai sebagai sumber |
| `pages_read` | Jumlah halaman dengan teks yang berhasil diekstrak |
| `chunks_stored` | Jumlah potongan yang dimasukkan ke Qdrant |

### `POST /ask`

Content type: `application/json`.

```json
{
  "question": "Apa rekomendasi utama dalam laporan ini?"
}
```

Contoh respons:

```json
{
  "answer": "Rekomendasi utama adalah **memperkuat pemantauan risiko**.",
  "sources": [
    {
      "source": "laporan.pdf",
      "page": 3,
      "score": 0.82
    }
  ]
}
```

Contoh PowerShell:

```powershell
$body = @{ question = 'Apa rekomendasi utama dalam laporan ini?' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/ask' -ContentType 'application/json' -Body $body
```

### `POST /brief`

Content type: `application/json`.

```json
{
  "topic": "Risiko operasional dan mitigasi"
}
```

Contoh respons:

```json
{
  "topic": "Risiko operasional dan mitigasi",
  "brief": "## Summary\nRingkasan topik.\n\n## Key Points\n- Poin utama.\n\n## Source References\n- laporan.pdf, halaman 3.",
  "sources": [
    {
      "source": "laporan.pdf",
      "page": 3,
      "score": 0.82
    }
  ]
}
```

Contoh PowerShell:

```powershell
$body = @{ topic = 'Risiko operasional dan mitigasi' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/brief' -ContentType 'application/json' -Body $body
```

### Respons kegagalan

| Status | Kondisi |
| --- | --- |
| `400` | Nama file kosong atau ekstensi bukan `.pdf` pada ingestion |
| `422` | Field wajib tidak dikirim atau tipe request tidak sesuai skema FastAPI |
| `500` | Kegagalan ekstraksi, embedding, penyimpanan, atau proses backend lain |

Ingestion mengembalikan pesan exception dalam field `detail`, misalnya:

```json
{
  "detail": "No readable text was found in the PDF."
}
```

Endpoint `/ask` dan `/brief` saat ini tidak membungkus exception dengan format error khusus. Kegagalan server dapat menghasilkan respons non-JSON; frontend menampilkannya sebagai pesan kegagalan umum. Field pertanyaan/topik wajib berupa string, tetapi validasi string kosong atau whitespace hanya dilakukan di frontend saat ini.

## Struktur proyek

```text
rag-learn/
├── main.py                     # Route API, halaman utama, dan static files
├── schemas.py                  # Model request pertanyaan dan brief
├── config.py                   # Environment, lokasi data, dan parameter RAG
├── rag.py                      # Ingestion, retrieval, prompt, dan referensi
├── pdf_loader.py               # Ekstraksi teks PDF per halaman
├── chunker.py                  # Pemecahan teks berbasis tokenizer
├── embeddings.py               # Inisialisasi model dan embedding
├── vector_store.py             # Koleksi, upsert, dan pencarian Qdrant lokal
├── llm.py                      # Integrasi async dengan Groq
├── requirements.txt            # Dependensi Python
├── .env.example                # Template konfigurasi
├── .gitignore
├── DESIGN-SKYNIGHT-SUBTLE.md    # Spesifikasi desain website
├── README.md
├── static/
│   ├── index.html              # Struktur website
│   ├── styles.css              # Token desain, komponen, dan gaya Markdown
│   ├── app.js                  # API client, upload, tab, dan renderer
│   └── vendor/                 # Marked, DOMPurify, dan lisensi
├── data/
│   └── uploads/                # PDF yang diunggah
└── qdrant_data/                # Database vektor lokal
```

## Penyimpanan dan siklus data

| Data | Lokasi | Perilaku |
| --- | --- | --- |
| PDF asli | `data/uploads/` | Disimpan sebelum ingestion dijalankan |
| Vektor, teks potongan, metadata | `qdrant_data/` | Persisten pada disk dan digunakan lintas sesi browser |
| Daftar upload frontend | `sessionStorage`, key `simple-rag-session-uploads` | Metadata upload untuk sesi tab; bukan daftar seluruh koleksi |
| Jawaban dan brief pada UI | Memori halaman / DOM | Hilang saat halaman dimuat ulang |
| Model dan tokenizer | Cache library Hugging Face | Diunduh ketika belum tersedia |

Tidak ada endpoint untuk daftar seluruh dokumen, unduh PDF, hapus dokumen, atau reset koleksi. Menghapus item dari penyimpanan browser tidak menghapus data backend. Menghapus PDF dari folder upload juga tidak otomatis menghapus potongan yang sudah tersimpan di Qdrant.

Upload ulang membuat point ID baru dan menambahkan potongan lagi, tanpa deduplikasi. Jika nama file sama, PDF pada disk ditimpa sementara potongan lama tetap ada dalam koleksi.

Untuk memulai knowledge base baru tanpa membuang data lama, hentikan server lalu ubah `QDRANT_PATH` ke direktori baru dalam `config.py`; setelah server dijalankan kembali, unggah dokumen yang diperlukan. Data lama tetap ada pada path sebelumnya.

## Kustomisasi

- **Warna, radius, font:** ubah token `:root` pada `static/styles.css`, dengan [spesifikasi desain](DESIGN-SKYNIGHT-SUBTLE.md) sebagai referensi.
- **Gaya tabel dan Markdown:** ubah selector `.markdown-body` dan `.markdown-table-scroll`.
- **Layout dan teks antarmuka:** edit `static/index.html`.
- **Perilaku API client:** edit `static/app.js`.
- **Prompt dan struktur respons:** edit system prompt di `rag.py`.
- **Model generasi:** ubah `GROQ_MODEL` dalam `.env` lalu restart server.
- **Jumlah konteks dan chunking:** ubah parameter di `config.py`. Perubahan chunking berlaku untuk ingestion baru; dokumen lama perlu diindeks ulang pada koleksi baru agar konsisten.
- **Library frontend:** informasi versi, sumber, dan lisensi tersedia di [static/vendor/README.md](static/vendor/README.md).

## Batasan aplikasi

- PDF berbasis gambar belum diproses dengan OCR.
- Pencarian memakai teks hasil ekstraksi, bukan pemahaman visual terhadap gambar atau layout tabel PDF.
- Seluruh dokumen memakai satu knowledge base; belum ada autentikasi, pemisahan pengguna, atau filter dokumen per pertanyaan.
- Tidak ada riwayat percakapan atau konteks pertanyaan sebelumnya yang dikirim ke LLM.
- Respons belum menggunakan streaming.
- Retrieval mengambil potongan terdekat tanpa threshold relevansi atau reranking.
- Prompt menginstruksikan LLM memakai konteks saja, tetapi kualitas jawaban tetap dipengaruhi retrieval dan perilaku model.
- File upload dibaca penuh ke memori, tanpa batas ukuran khusus pada kode aplikasi.
- Ingestion menjalankan ekstraksi dan embedding secara sinkron dalam handler; belum ada antrean background.
- Qdrant lokal dipakai oleh satu proses. Deployment multiproses membutuhkan perubahan arsitektur penyimpanan.
- Dependensi Python dalam `requirements.txt` belum dipin ke versi tertentu.
- Aplikasi belum menyediakan kontrol akses dan pembatasan permintaan untuk layanan publik.

## Pemecahan masalah

### `GROQ_API_KEY` belum diisi atau ditolak

Isi API key pada `.env` di root proyek, pastikan key aktif, lalu restart server. Jangan menaruh key di file frontend atau membagikan `.env`.

### Model Groq tidak tersedia / rate limit

Gunakan model yang dapat diakses akun Anda melalui `GROQ_MODEL`. Untuk rate limit, tunggu sebelum mengirim ulang dan perhatikan batas akun. Detail exception dapat dilihat pada terminal server.

### Startup lama atau pengunduhan model gagal

Pastikan koneksi internet tersedia dan cache model dapat ditulis. Model embedding serta tokenizer dimuat saat modul backend diimpor, sehingga website belum tersedia sebelum inisialisasi selesai.

### `No readable text was found in the PDF.`

Dokumen tidak menghasilkan teks yang dapat diproses. Gunakan PDF berbasis teks atau lakukan OCR terlebih dahulu. PDF rusak atau terenkripsi juga dapat memerlukan perbaikan sebelum diunggah.

### Direktori Qdrant sedang dipakai

Hentikan proses lain yang memakai `qdrant_data/`. Jalankan satu instance backend dengan satu worker untuk penyimpanan lokal.

### Daftar upload kosong setelah menutup tab

Daftar UI berasal dari sesi tab browser. Koleksi backend tetap ada di disk dan masih dapat ditelusuri melalui pertanyaan atau brief.

### Respons kurang relevan

Gunakan pertanyaan lebih spesifik, pastikan teks PDF dapat diekstrak, dan perhatikan sumber yang dikembalikan. Sesuaikan parameter retrieval atau gunakan knowledge base baru yang lebih fokus bila dokumen bercampur.

### Markdown masih muncul sebagai teks biasa

Muat ulang halaman setelah perubahan asset frontend. Pastikan file `static/vendor/marked.umd.js` dan `static/vendor/purify.min.js` ikut disalin ketika memindahkan proyek. Fallback teks digunakan bila library tidak termuat. Agar tabel dirender, output harus memakai sintaks tabel Markdown yang valid.

### Tampilan font berbeda

Font berasal dari Google Fonts. Jika akses jaringan ke layanan tersebut tidak tersedia, browser menggunakan font fallback; fungsi aplikasi dan rendering Markdown lokal tetap tersedia.
