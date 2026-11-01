# RAG Parameter Exploration

Seluruh output di bawah berasal dari aplikasi yang benar-benar dijalankan (FastAPI + Qdrant lokal + Groq `openai/gpt-oss-120b`). Data mentah (JSON) ada di `hasil_eksperimen/results.json`. Eksperimen dijalankan otomatis oleh `hasil_eksperimen/run_experiments.py`: untuk tiap konfigurasi skrip mengubah `config.py` / `llm.py`, **menghapus `qdrant_data/`**, menjalankan server baru, memanggil `POST /ingest` lalu `POST /ask`. Setelah selesai, nilai parameter dikembalikan ke default.

## Informasi Eksperimen

Nama PDF: `rag_intro.pdf` (di `data/rag_intro.pdf`, dibuat dengan `hasil_eksperimen/make_pdf.py`)

Jumlah halaman PDF: 3

Isi / topik PDF secara singkat: pengantar RAG, chunking & embedding, vector database, serta parameter TOP_K dan temperature. PDF berbasis teks (bukan scan).

### Pertanyaan Pengujian

**Pertanyaan 1:** Apa fungsi chunk overlap dan mengapa penting?
(jawaban ada di halaman 2)

**Pertanyaan 2:** Berapa dimensi vektor model paraphrase-multilingual-MiniLM-L12-v2 dan berapa batas maksimum token inputnya?
(jawaban ada di halaman 2: 384 dimensi, 128 token)

## Baseline Configuration

| Parameter | Nilai |
|---|---|
| Temperature | 0.2 |
| TOP_K | 4 |
| Chunk Size | 100 |
| Chunk Overlap | 20 |
| Embedding Model | sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| LLM Model | openai/gpt-oss-120b (Groq) |

Baseline menghasilkan `chunks_stored = 9`.

### Catatan metodologi

- Field `sources` pada response `/ask` **dideduplikasi per halaman** (`build_sources` di `rag.py`), dan skor yang tampil adalah skor chunk terbaik pada halaman itu. Karena PDF hanya 3 halaman, daftar source maksimal berisi 3 entri walau TOP_K lebih besar. Jumlah chunk sebenarnya yang dikirim ke LLM = TOP_K, tetapi tidak terlihat langsung di response.
- Di `chunker.py` dan `rag.py`, separator ditulis `"\\n\\n"` (backslash literal, bukan newline). Kode ini **tidak diubah** agar sama dengan repo asli. Konsekuensinya separator paragraf tidak bekerja dan pemisahan lebih banyak jatuh ke `". "` / spasi.
- Experiment 1 dijalankan 2 kali per pertanyaan untuk melihat konsistensi. Eksperimen lain dijalankan 1 kali per pertanyaan, jadi perbedaan kecil pada wording antar eksperimen bisa saja berasal dari variasi sampling LLM (temperature 0.2), bukan dari parameter yang diubah. Skor similarity bersifat deterministik, sehingga lebih dapat diandalkan sebagai bukti.
- Port 8000 di mesin ini dipakai aplikasi lain, sehingga eksperimen dijalankan di port 8765.

## Experiment 1 - Temperature

TOP_K=4, Chunk Size=100, Overlap=20, `chunks_stored=9`. Sources & skor sama di semua temperature: Q1 = hal 2 (0.532), hal 1 (0.376), hal 3 (0.370); Q2 = hal 2 (0.853), hal 3 (0.502), hal 1 (0.444).

### Temperature = 0.0

**Actual Output**

Q1 (run 1): Chunk overlap berfungsi untuk menyalin sebagian teks secara sengaja ke dua chunk yang bersebelahan, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Hal ini penting karena mencegah hilangnya informasi penting di perbatasan chunk dan menjaga konteks agar tidak terfragmentasi. **Sumber:** rag_intro.pdf, hal 2.

Q1 (run 2): Chunk overlap berfungsi untuk menyalin sebagian teks secara sengaja **di antara** dua chunk yang bersebelahan, sehingga kalimat yang terpotong ... (kalimat selanjutnya identik dengan run 1).

Q2 (run 1 dan 2, identik): Model **paraphrase‑multilingual‑MiniLM‑L12‑v2** menghasilkan vektor berdimensi **384** dan memiliki batas maksimum input **128 token**. *Source: rag_intro.pdf, Page 2*

**Observation**

Jawaban Q2 identik kata per kata di dua run. Jawaban Q1 hampir identik (hanya "ke dua chunk" vs "di antara dua chunk"). Ini paling stabil dari ketiga nilai, tetapi tidak 100% deterministik pada Q1.

### Temperature = 0.2

**Actual Output**

Q1 (run 1): Chunk overlap berfungsi untuk mengulang sebagian teks di antara dua chunk yang bersebelahan, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Hal ini penting karena mencegah hilangnya informasi penting di perbatasan chunk dan menjaga konteks tetap terjaga【Source: rag_intro.pdf | Page: 2】.

Q1 (run 2): Chunk overlap berfungsi untuk mengulang sebagian teks di antara dua chunk yang bersebelahan. Dengan cara ini, kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk, sehingga informasi penting tidak hilang di perbatasan — menjaga kontinuitas konteks dan meningkatkan kualitas pencarian. **Sumber:** rag_intro.pdf, hal 2.

Q2 (run 1): ... vektor berdimensi **384** dan memiliki batas maksimum **128 token** untuk input teks. *Source: rag_intro.pdf, halaman 2*

Q2 (run 2): ... vektor berdimensi **384** dan memiliki batas panjang input maksimal **128 token**. *Source: rag_intro.pdf, Page 2*

**Observation**

Struktur kalimat dan format sitasi mulai bervariasi antar run (`【Source: ... 】` vs `**Sumber:**`). Fakta (384 dimensi, 128 token, halaman 2) tetap sama.

### Temperature = 0.8

**Actual Output**

Q1 (run 1): Chunk overlap berfungsi untuk menyalin sebagian teks di antara dua chunk yang bersebelahan sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Dengan cara ini informasi penting tidak hilang di perbatasan chunk, menjaga konteks dan meningkatkan kualitas pencarian serta pemahaman LLM. **Sumber:** rag_intro.pdf, hal 2.

Q1 (run 2): Chunk overlap berfungsi untuk mengulang sebagian teks di antara dua chunk yang bersebelahan. Dengan begitu, kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk, sehingga informasi penting tidak hilang di perbatasan. Hal ini penting karena menjaga kelengkapan konteks dan mencegah kehilangan makna saat dokumen di‑chunking【Source: rag_intro.pdf | Page: 2】.

Q2 (run 1): ... **384** dan memiliki batas maksimum **128 token** untuk inputnya. *Source: rag_intro.pdf, Page 2*

Q2 (run 2): ... vektor dengan **dimensi 384** dan memiliki **batas maksimum input 128 token**. *Source: rag_intro.pdf, Page 2*

**Observation**

Wording paling beragam (misalnya frasa "pemahaman LLM" dan "dokumen di‑chunking" muncul, yang merupakan parafrase bebas dan tidak persis ada di PDF). Informasi inti tetap benar karena konteks pendek dan jelas.

### Kesimpulan Experiment Temperature

**Apa perubahan yang paling terlihat?** Wording dan variasi antar run. Pada temperature 0.0 jawaban hampir identik antar run; pada 0.2 dan 0.8 kalimat berbeda-beda. Panjang jawaban tidak berubah secara konsisten, dan fakta tidak berubah pada eksperimen ini.

**Nilai yang paling cocok:** 0.0 (atau 0.2 sebagai kompromi).

**Kenapa?** RAG bertujuan menjawab berdasarkan dokumen, bukan berkreasi. Nilai rendah memberi jawaban yang konsisten dan lebih mudah diverifikasi. Pada 0.8 terlihat parafrase yang menambah frasa di luar teks sumber, sehingga ada risiko menyimpang walau pada pertanyaan ini belum terjadi kesalahan fakta.

## Experiment 2 - TOP_K

Temperature=0.2, Chunk Size=100, Overlap=20, `chunks_stored=9`.

### TOP_K = 1

**Actual Output**

Q1: Chunk overlap berfungsi untuk memastikan bahwa kalimat yang terpotong pada batas‑batas chunk tetap utuh di salah satu chunk. Dengan begitu, informasi penting tidak hilang di perbatasan chunk. (Sumber: rag_intro.pdf, halaman 2)

Q2: Model **paraphrase‑multilingual‑MiniLM‑L12‑v2** menghasilkan vektor berdimensi **384** dan memiliki batas maksimum **128 token** untuk inputnya. (Sumber: rag_intro.pdf, halaman 2)

**Sources / Similarity Score**

Q1: hal 2 (0.532). Q2: hal 2 (0.853).

**Observation**

Hanya 1 chunk yang dikirim ke LLM dan itu sudah cukup untuk kedua pertanyaan. Jawaban Q1 lebih ringkas dan tidak menyebut bahwa overlap menjaga konteks secara umum.

### TOP_K = 4

**Actual Output**

Q1: Chunk overlap berfungsi untuk mengulang sebagian teks di antara dua chunk yang bersebelahan, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Hal ini penting karena mencegah hilangnya informasi penting di perbatasan chunk dan menjaga konteks tetap lengkap untuk proses pencarian dan retrieval. **Sumber:** rag_intro.pdf, halaman 2.

Q2: Model **paraphrase‑multilingual‑MiniLM‑L12‑v2** menghasilkan vektor berdimensi **384** dan memiliki batas panjang input maksimum **128 token**. *Source: rag_intro.pdf, halaman 2*

**Sources / Similarity Score**

Q1: hal 2 (0.532), hal 1 (0.376), hal 3 (0.370). Q2: hal 2 (0.853), hal 3 (0.502), hal 1 (0.444).

**Observation**

Dengan 4 chunk, sources memuat 3 halaman. Jawaban lengkap dan menjawab "fungsi" serta "mengapa penting".

### TOP_K = 8

**Actual Output**

Q1: Chunk overlap berfungsi untuk menambahkan bagian teks yang sama pada dua chunk yang bersebelahan. Dengan cara ini, kalimat yang terpotong di batas chunk tetap utuh di salah satu chunk, sehingga informasi penting tidak hilang di perbatasan — menjaga konteks dan kelengkapan data yang akan di‑embed. **Sumber:** rag_intro.pdf, hal 2.

Q2: Model **paraphrase‑multilingual‑MiniLM‑L12‑v2** menghasilkan vektor berdimensi **384** dan memiliki batas maksimum **128 token** untuk inputnya. *Source: rag_intro.pdf, Page 2*

**Sources / Similarity Score**

Q1: hal 2 (0.532), hal 1 (0.376), hal 3 (0.370). Q2: hal 2 (0.853), hal 3 (0.502), hal 1 (0.444). (Sama dengan TOP_K=4 karena sources dideduplikasi per halaman; 8 dari 9 chunk yang tersimpan dikirim ke LLM.)

**Observation**

Tidak ada peningkatan kualitas dibanding TOP_K=4. Hampir seluruh dokumen ikut masuk konteks, sehingga banyak chunk tidak relevan terkirim (lebih banyak token), namun jawaban tetap benar.

### Kesimpulan Experiment TOP_K

**Apakah TOP_K yang lebih besar selalu lebih baik?** Tidak. Dari 4 ke 8 jawaban tidak membaik, hanya konteks yang membengkak. Pada dokumen kecil ini, TOP_K=1 pun sudah cukup untuk fakta tunggal, tetapi jawaban lebih tipis.

**TOP_K paling cocok:** 4.

**Kenapa?** Memberi cukup konteks untuk jawaban yang lengkap tanpa mengirim hampir seluruh dokumen ke LLM.

## Experiment 3 - Chunk Size

Overlap=20, TOP_K=4, Temperature=0.2.

### Chunk Size = 50

**Chunks Stored:** 20

**Actual Output**

Q1: Chunk overlap berfungsi untuk menyalin bagian teks yang berada di tepi satu chunk ke chunk berikutnya, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Dengan cara ini informasi penting tidak hilang di perbatasan chunk, menjaga konteks dan meningkatkan kualitas pencarian. **Sumber:** rag_intro.pdf, halaman 2.

Q2: Model ... berdimensi **384** dan memiliki batas maksimum **128 token** untuk inputnya. *Source: rag_intro.pdf, halaman 2.*

**Sources / Similarity Score**

Q1: hal 2 (0.588), hal 3 (0.494). Q2: hal 2 (0.789), hal 3 (0.446).

**Observation**

Chunk jumlahnya lebih dari dua kali lipat. Skor Q1 lebih tinggi (0.588 vs 0.532) karena chunk lebih terfokus, tetapi skor Q2 turun (0.789 vs 0.853) karena informasi 384 dimensi dan 128 token terbelah ke chunk berbeda. Keempat chunk teratas hanya berasal dari halaman 2 dan 3. Jawaban tetap benar pada kedua pertanyaan.

### Chunk Size = 100

**Chunks Stored:** 9

**Actual Output**

Q1: Chunk overlap berfungsi untuk menyalin sebagian teks di antara dua chunk yang bersebelahan, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Dengan cara ini informasi penting tidak hilang di perbatasan chunk, menjaga kontinuitas konteks dan meningkatkan kualitas pencarian serta pemahaman model RAG【Source: rag_intro.pdf | Page: 2】.

Q2: ... **384** dan memiliki batas maksimum input **128 token**. *(Sumber: rag_intro.pdf, halaman 2)*

**Sources / Similarity Score**

Q1: hal 2 (0.532), hal 1 (0.376), hal 3 (0.370). Q2: hal 2 (0.853), hal 3 (0.502), hal 1 (0.444).

**Observation**

Baseline. Skor Q2 0.853 (sama dengan size 120, lebih tinggi dari size 50).

### Chunk Size = 120

**Chunks Stored:** 7

**Actual Output**

Q1: Chunk overlap berfungsi untuk menambahkan bagian teks yang sama pada dua chunk yang bersebelahan. Dengan cara ini, kalimat atau frasa yang terpotong di batas chunk tetap utuh di salah satu chunk, sehingga informasi penting tidak hilang pada perbatasan. Hal ini penting karena menjaga kontinuitas konteks dan mencegah kehilangan makna ketika dokumen di‑chunk menjadi potongan‑potongan kecil. **Sumber:** rag_intro.pdf, halaman 2.

Q2: ... **384** dan memiliki batas maksimum **128 token** untuk inputnya. *Sumber: rag_intro.pdf, halaman 2.*

**Sources / Similarity Score**

Q1: hal 2 (0.523), hal 1 (0.376), hal 3 (0.370). Q2: hal 2 (0.853), hal 3 (0.502), hal 1 (0.444).

**Observation**

Chunk lebih sedikit. Skor hampir sama dengan size 100 (Q1 0.523 vs 0.532, Q2 sama). Jawaban benar dan sedikit lebih lengkap pada Q1.

### Kesimpulan Experiment Chunk Size

**Hubungan Chunk Size dengan jumlah chunk:** berbanding terbalik. 50 → 20 chunk, 100 → 9 chunk, 120 → 7 chunk.

**Apakah chunk lebih kecil selalu retrieval lebih baik?** Tidak. Skor Q1 naik di size 50 tetapi skor Q2 turun, dan hasil retrieval jadi lebih sempit (hanya 2 halaman).

**Chunk Size paling cocok:** 100.

**Kenapa?** Skor Q2 setara size 120 (0.853) dan lebih tinggi dari size 50, skor Q1 (0.532) sedikit di atas size 120, dan sources mencakup 3 halaman. Size 100 dan 120 hampir setara; perbedaannya kecil pada PDF sekecil ini.

## Experiment 4 - Chunk Overlap

Chunk Size=100, TOP_K=4, Temperature=0.2.

### Chunk Overlap = 0

**Chunks Stored:** 9

**Actual Output**

Q1: Chunk overlap berfungsi untuk mengulang sebagian teks di antara dua chunk yang bersebelahan, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Hal ini penting karena mencegah hilangnya informasi penting di perbatasan chunk dan menjaga konteks tetap lengkap untuk pencarian dan pemrosesan selanjutnya【Source: rag_intro.pdf | Page: 2】.

Q2: ... **384** dan memiliki batas panjang input maksimum **128 token**. *Source: rag_intro.pdf, Page 2*

**Sources / Similarity Score**

Q1: hal 2 (0.532), hal 1 (0.376), hal 3 (0.370). Q2: hal 2 (0.857), hal 3 (0.502), hal 1 (0.444).

**Observation**

Jumlah chunk sama dengan overlap 20. Skor Q2 sedikit lebih tinggi (0.857 vs 0.853), selisih sangat kecil.

### Chunk Overlap = 20

**Chunks Stored:** 9

**Actual Output**

Q1: Chunk overlap berfungsi untuk menyalin sebagian teks secara sengaja di antara dua chunk yang bersebelahan, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Hal ini penting karena mencegah hilangnya informasi penting di perbatasan chunk dan menjaga konteks tetap terjaga【rag_intro.pdf | Page 2】.

Q2: ... **384** dan memiliki batas panjang input maksimum **128 token**. *Source: rag_intro.pdf, halaman 2*

**Sources / Similarity Score**

Q1: hal 2 (0.532), hal 1 (0.376), hal 3 (0.370). Q2: hal 2 (0.853), hal 3 (0.502), hal 1 (0.444).

**Observation**

Baseline.

### Chunk Overlap = 40

**Chunks Stored:** 10

**Actual Output**

Q1: Chunk overlap berfungsi untuk menyalin sebagian teks di akhir satu chunk ke awal chunk berikutnya, sehingga kalimat yang terpotong pada batas chunk tetap utuh di salah satu chunk. Hal ini penting karena … menjaga agar informasi penting tidak hilang di perbatasan chunk dan mempertahankan konteks yang diperlukan untuk pencarian dan pemahaman LLM【Source: rag_intro.pdf | Page: 2】. (Tanda "…" muncul persis seperti ini pada output aplikasi.)

Q2: ... **384** dan memiliki batas maksimum input **128 token**. *Source: rag_intro.pdf, halaman 2*

**Sources / Similarity Score**

Q1: hal 2 (0.532), hal 3 (0.370), hal 1 (0.291). Q2: hal 2 (0.853), hal 3 (0.502), hal 1 (0.451).

**Observation**

Chunk bertambah menjadi 10 (naik 1). Skor halaman 1 untuk Q1 turun (0.376 → 0.291) sehingga urutan berubah: hal 3 mengungguli hal 1. Ini menunjukkan batas chunk bergeser dan isi chunk berubah. Kualitas jawaban tidak berbeda.

### Kesimpulan Experiment Chunk Overlap

**Pengaruh yang terlihat:** pengaruhnya kecil pada PDF ini. Jumlah chunk hanya berubah dari 9 menjadi 10 pada overlap 40, dan pada overlap 0 dan 20 jumlahnya sama. Overlap 40 menggeser skor beberapa halaman. Jawaban akhir tidak berubah secara bermakna.

**Apakah overlap lebih besar selalu lebih baik?** Tidak. Overlap 40 tidak memperbaiki jawaban, hanya menambah chunk duplikat (lebih banyak penyimpanan/embedding) dan mengubah skor Q1 untuk hal 1 menjadi lebih rendah.

**Nilai paling cocok:** 20.

## Final Configuration

| Parameter | Nilai |
|---|---|
| Temperature | 0.0 |
| TOP_K | 4 |
| Chunk Size | 100 |
| Chunk Overlap | 20 |

Catatan: konfigurasi ini dipilih dari hasil per-eksperimen di atas. Kombinasi final (termasuk temperature 0.0) tidak dijalankan sebagai satu run tersendiri.

## Final Questions

**1. Parameter mana yang paling terasa memengaruhi hasil aplikasi?** Chunk Size, karena mengubah jumlah chunk paling besar (9 → 20 atau 7) dan mengubah skor/halaman yang ditemukan. TOP_K memengaruhi banyaknya konteks yang dikirim. Temperature hanya memengaruhi wording.

**2. Apakah Temperature memengaruhi Retrieval atau Generation?** Generation saja. Pada seluruh run Experiment 1, sources dan skor similarity identik di 0.0, 0.2, dan 0.8, sedangkan wording jawaban berubah. Retrieval (embedding + pencarian vektor) terjadi sebelum LLM dipanggil.

**3. Apakah TOP_K yang lebih besar selalu lebih baik?** Tidak. TOP_K=8 tidak lebih baik dari TOP_K=4 pada pertanyaan ini, hanya mengirim hampir seluruh dokumen (8 dari 9 chunk) ke LLM.

**4. Apa yang terjadi ketika Chunk Size lebih kecil?** Jumlah chunk naik (20 pada size 50), chunk lebih terfokus sehingga skor Q1 naik, tetapi informasi yang berdekatan (dimensi 384 dan batas 128 token) bisa terpisah sehingga skor Q2 turun. Hasil retrieval juga lebih sempit (hanya hal 2 dan 3).

**5. Fungsi Chunk Overlap setelah eksperimen:** menjaga teks di perbatasan chunk agar tidak terputus, dengan menduplikasi sebagian akhir chunk ke chunk berikutnya. Pada PDF kecil ini efeknya tidak besar (chunk 9 → 9 → 10), jadi manfaat nyatanya tidak terbukti kuat di sini. Fungsinya lebih terlihat di teori daripada di data ini.

**6. Kenapa perubahan Chunk Size dan Overlap butuh ingestion ulang?** Keduanya dipakai saat tahap chunking, sebelum embedding dan penyimpanan. Chunk dan vektor yang sudah tersimpan di Qdrant tetap berasal dari ukuran lama. Mengubah konfigurasi tidak mengubah data yang sudah ada, sehingga PDF harus dipotong dan di-embed ulang, dan `qdrant_data/` dihapus agar chunk lama tidak tercampur.

**7. Kenapa perubahan Temperature tidak butuh ingestion ulang?** Temperature hanya dipakai saat memanggil LLM untuk membuat jawaban. Ia tidak memengaruhi chunk atau vektor di Qdrant.

**8. Apakah ada satu konfigurasi yang selalu terbaik untuk semua dokumen?** Tidak. Hasil di atas hanya valid untuk PDF pendek 3 halaman ini. Dokumen yang lebih panjang, berstruktur tabel, atau pertanyaan yang butuh gabungan banyak bagian kemungkinan membutuhkan TOP_K, chunk size, dan overlap yang berbeda.

## Personal Reflection

**Bagian eksperimen mana yang hasilnya paling berbeda dari dugaan kalian?**

Experiment Chunk Overlap. Saya mengira overlap akan jelas mengubah jumlah chunk dan kualitas jawaban, tetapi overlap 0 dan 20 menghasilkan jumlah chunk yang sama (9), dan overlap 40 hanya menambah 1 chunk (10). Jawaban juga tidak berbeda secara bermakna. Hal lain yang di luar dugaan: TOP_K=8 tidak memperbaiki jawaban dibanding TOP_K=4, hanya mengirim hampir seluruh dokumen ke LLM.

**Parameter mana yang awalnya kalian anggap tidak terlalu penting tetapi ternyata berpengaruh?**

Chunk Size. Awalnya saya anggap ini hanya soal pemotongan teks, tetapi ternyata mengubah jumlah chunk paling besar (9 menjadi 20 pada size 50), mengubah skor similarity, dan mengubah halaman mana yang muncul di hasil retrieval. Pada size 50 informasi "384 dimensi" dan "128 token" cenderung terpisah sehingga skor Q2 turun (0.853 menjadi 0.789).

**Setelah mengerjakan tugas ini, bagaimana kalian menjelaskan hubungan antara Retrieval dan Generation pada RAG?**

Retrieval menentukan konteks apa yang dilihat LLM: saat chunking atau TOP_K berubah, sources dan skor berubah. Generation menentukan bagaimana konteks itu diungkapkan: saat temperature berubah, wording berubah tetapi sources dan skor tetap sama. Kualitas jawaban dibatasi oleh kualitas retrieval, karena LLM hanya diminta menjawab dari konteks yang diberikan. Jika chunk yang relevan tidak terambil, LLM tidak punya bahan untuk menjawab dengan benar.

**Jika aplikasi ini dikembangkan lebih lanjut, parameter atau bagian apa lagi yang ingin kalian coba?**

Memperbaiki separator `"\\n\\n"` di `chunker.py` (saat ini backslash literal) lalu membandingkan hasilnya, menampilkan skor per chunk tanpa dedupe per halaman agar efek TOP_K terlihat langsung, mencoba model embedding lain, memakai PDF yang lebih panjang dengan pertanyaan yang jawabannya tersebar di beberapa bagian, dan menguji BRIEF_TOP_K pada endpoint `/brief`.

## AI Usage

**AI tools yang digunakan:** Claude Code (Claude Sonnet 5.5).

**AI digunakan untuk membantu bagian apa?** Setup project (clone, venv, install), membuat PDF contoh, menulis skrip yang menjalankan 12 konfigurasi eksperimen secara otomatis, dan menyusun draf README dari hasil JSON yang dihasilkan aplikasi.

**Bagian eksperimen mana yang kalian lakukan dan evaluasi sendiri?**

Menyiapkan GROQ API key dan file `.env`, menentukan pertanyaan pengujian dan memilih topik PDF, meninjau hasil eksperimen dari aplikasi, serta menentukan Final Configuration dan menjawab Final Questions berdasarkan hasil tersebut. Eksekusi otomatis 12 konfigurasi dilakukan oleh skrip yang disusun dengan bantuan AI.
