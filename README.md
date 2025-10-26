# proyek-tengah-semester
Kelompok F11 - PBP F

## 1. Nama-nama anggota kelompok

1. Ganesha Taqwa
2. Tazkia Nur Alyani
3. Josiah Naphta Simorangkir
4. Muhammad Rafi Ghalib Fideligo
5. Naufal Zafran Fadil
6. Prama Ardend Narendradhipa

## 2. Deskripsi aplikasi (cerita aplikasi yang diajukan serta kebermanfaatannya)
Vacathon adalah sebuah platform digital berbasis web yang kami kembangkan untuk menjembatani para penggemar dan juga penyelenggara marathon dengan semangat petualangan (Vacation). Kami hadir untuk menjadi wadah yang memfasilitasi setiap aspek mulai dari perencanaan, pendaftaran, hingga partisipasi dalam acara marathon, baik di track yang sudah terkenal, maupun di lokasi-lokasi baru yang menantang di seluruh dunia.

Selama ini, proses pencarian dan pendaftaran marathon sering kali tersebar di berbagai situs atau media sosial yang terkadang menyulitkan pelari untuk mendapatkan informasi yang terpusat, akurat, dan terpercaya. Website Vacathon ini didesain untuk melayani dua kelompok utama: para pelari yang ingin menemukan dan mendaftar event dengan mudah, serta penyelenggara yang ingin mengajukan dan mengelola event mereka secara efisien. Dengan adanya fitur pencarian yang mendetail (berdasarkan jarak, lokasi, waktu), tampilan detail maraton yang lengkap (rute, cut-off time, titik istirahat), serta forum diskusi untuk komunitas pelari, kami ingin meningkatkan pengalaman marathon dari sekadar balapan menjadi perjalanan yang terencana dan berkesan.

Visi kami adalah menjadikan Vacathon sebagai destinasi utama bagi komunitas pelari global. Kami menyediakan solusi "Discover" bagi pelari yang ingin menemukan marathon berdasarkan kriteria spesifik seperti jarak, lokasi, dan tanggal acara. Kami juga menawarkan fitur "Host Events" yang memfasilitasi individu atau kelompok tertentu untuk merencanakan dan menyelenggarakan acara marathon mereka sendiri, dengan proses pengajuan (request) yang terstruktur dan divalidasi oleh Admin untuk memastikan kualitas dan keamanan.




## 3. Daftar modul yang akan diimplementasikan
### 1. Main Menu
  1. Banner utama berisi highlight event
  2. Navigasi ke halaman lain:
    - Daftar Marathon (event list)
    - Forum Diskusi
    - Akun Saya
    - Tentang Kami/Kontak
  3. Menampilkan statistik singkat: jumlah peserta, lokasi aktif, sponsor, dll.
  4. Tombol “Daftar Sekarang” untuk event tertentu.
  5. Video mengenai marathon
  6. News mengenai marathon
  7. Dekripsi singkat mengenai vacathon dan juga developer-nya
  8. Penghubung dengan aplikasi lain

### 2. Daftar Event (Event Catalog)
  Tampilan Daftar Event:
  1. Menampilkan semua event (Upcoming, Ongoing, Completed) dalam format list atau card view.
  2. Setiap item event menampilkan informasi ringkas (Nama, Tanggal, Lokasi) dan tombol "Lihat Detail".

  Fitur Pencarian:
  1. Menyediakan bar pencarian (search bar) untuk mencari event berdasarkan nama atau keyword.

  Fungsionalitas Filter (Penyaringan):
  1. User dapat menyaring daftar event berdasarkan kriteria spesifik.
  2. Filter berdasarkan Jarak lari: 5K, 10K, 21K, 42K, Ultra Marathon.
  3. Filter berdasarkan Lokasi/Kota: (misal: Jakarta, Bandung, Bali, Surabaya, dll).
  4. Filter berdasarkan Tanggal/Waktu: rentang tanggal atau bulan tertentu.
  5. Filter berdasarkan Status Event: Upcoming / Ongoing / Completed.
  6. Mendukung kemampuan multi-filter (menggabungkan beberapa kriteria filter sekaligus).

  Fungsionalitas Sorting (Pengurutan):
  1. User dapat mengurutkan daftar event yang ditampilkan.
  2. Sorting berdasarkan Terpopuler (jumlah peserta terbanyak).
  3. Sorting berdasarkan Tanggal terdekat.
  4. Sorting berdasarkan Lokasi terdekat (opsional jika ada data geolokasi).

  Kontrol Tampilan:
  1. Tombol Reset Filter untuk menghapus semua filter yang aktif dan mengembalikan tampilan ke daftar semua event.
  2. Paginasi (Halaman 1, 2, 3, ...) untuk mengelola daftar event yang panjang agar tidak dimuat sekaligus.
    
        
### 3. Detail Marathon
  1. Informasi utama:
     1. Nama event, deskripsi singkat
     2. Lokasi (dengan peta interaktif opsional)
     3. Tanggal & waktu pelaksanaan
     4. Flag-off time (jam mulai)
     5. Cut-off time (batas waktu finish)
     6. Jumlah peserta terdaftar & kapasitas maksimum
     7. Biaya pendaftaran dan kategori lomba

  2. Detail rute:
     1. Total jarak
     2. Titik start dan finish
     3. Titik istirahat / water station
     4. Peta rute (opsional google maps)

  3. Tombol “Daftar Sekarang” jika belum mendaftar
  4. Tombol “Lihat Forum Event Ini” untuk berdiskusi khusus event tersebut
  5. Tombol “Lihat Peserta” (khusus admin)

### 4. Forum Diskusi
  1. Daftar topik per event (thread per event).
  2. Fitur search untuk mencari topik atau komentar.
  3. User bisa:
       - Membuat posting baru
       - Membalas komentar
       - Memberi like atau upvote
       - Melaporkan posting (report) jika tidak pantas
  4. Admin bisa:
       - Menghapus komentar/post tidak pantas
       - Menandai posting penting (pinned post)
  5. Tampilan user-friendly seperti forum pada umumnya.

### 5. Page Account (Admin & User Biasa)
  1. Untuk user biasa:
     1. Profil user (nama, email, kota, nomor telp, gender, usia, dll).
     2. Riwayat pendaftaran event marathon:
       1. Event yang diikuti
       2. Status pembayaran
       3. Nomor BIB (jika sudah diterbitkan)
       4. Waktu finish (jika sudah selesai lomba)
     3. Edit profil & ubah password
     4. Riwayat forum activity (post & komentar yang dibuat)
        
  2. Untuk admin:
     1. Dashboard statistik:
        1. Jumlah total peserta
        2. Jumlah event aktif & selesai
        3. Laporan jumlah peserta per event
     2. CRUD Event Marathon (Create, Read, Update, Delete).
     3. Kelola data peserta:
        1. Konfirmasi pendaftaran
        2. Validasi pembayaran
        3. Generate BIB Number
     4. Moderasi forum (hapus posting, blok user)
     5. Laporan dan ekspor data (CSV/ Excel)

### 6. Form Pendaftaran
  1. Pilih event yang akan diikuti
  2. Isi data pribadi peserta:
     1. Nama lengkap
     2. Tanggal lahir / usia
     3. Jenis kelamin
     4. Nomor HP dan email
     5. Alamat
  3. Pilih kategori lomba (misal: 5K / 10K / 21K).
  4. Unggah bukti pembayaran (jika event berbayar).
  5. Tombol “Submit” untuk mengirim pendaftaran.
  6. Notifikasi status pendaftaran: “Menunggu konfirmasi”, “Diterima”, atau “Ditolak”.
  7. Admin menerima notifikasi pendaftaran baru untuk diverifikasi.

## 4. Sumber initial dataset kategori utama produk
### Link: https://www.kaggle.com/datasets/aiaiaidavid/the-big-dataset-of-ultra-marathon-running/data?select=TWO_CENTURIES_OF_UM_RACES.csv (dengan modifikasi)


## 5. Role atau peran pengguna beserta deskripsinya (karena bisa saja lebih dari satu jenis pengguna yang mengakses aplikasi)
 ### 1. Main menu
    user biasa: - Akses ke menu utama (home, filter, detail, forum, account, form pendaftaran). 
                - Navigasi antar halaman.
    admin: - Sama seperti user. 
           - Bisa mengatur tampilan menu (menambah, menghapus, atau menyembunyikan fitur tertentu). 
           - Mengatur urutan atau prioritas menu.
     
  ###  2. Filter event marathon
    user biasa: Menggunakan filter untuk mencari event berdasarkan: 
                • Lokasi
                • Jarak lomba (5K, 10K, 21K, 42K) 
                • Waktu/event terdekat atau terjauh.
    admin: - Menyediakan data marathon agar bisa difilter (menginput data event dengan atribut lengkap). 
           - Menentukan kategori filter apa saja yang tersedia
     
   ### 3. Detail marathon
    user biasa: - Melihat detail event: lokasi, rute, checkpoint, tanggal, kuota peserta, biaya, hadiah. 
                - Klik “Daftar” untuk ikut event. 
                - Bisa share event ke forum/media sosial.
    admin: - Membuat event baru (lengkap dengan lokasi, rute, checkpoint, jadwal). 
           - Mengedit / menghapus event. 
           - Menutup atau membuka pendaftaran.
           - Upload peta interaktif, poster, atau dokumen panduan lomba.
     
  ### 4. Forum diskusi
    user biasa: - Membuat posting (pengalaman, tips, review event). 
                - Membalas/komentar pada posting user lain. 
                - Like / react pada posting.
    admin: - Mengelola forum (hapus komentar/postingan yang melanggar aturan). 
           - Bisa membuat thread khusus untuk pengumuman resmi. 
           - Bisa “pin” posting penting.

   ### 5. Page account
    user biasa: - Edit profil (nama, foto, bio, kontak, password). 
                - Melihat history lomba yang sudah pernah diikuti. 
                - Cek status pendaftaran event (pending, approved, paid)
    admin: - Edit profil admin sendiri. 
           - Melihat & mengelola data semua user. - Bisa reset password user.
           - Bisa suspend/ban akun user. 
           - Melihat rekap history lomba per user (untuk keperluan verifikasi atau laporan).

  ### 6. Form pendaftaran lomba
    user biasa: - Mengisi form untuk daftar lomba (nama, kategori, data diri).
                - Melihat status pendaftaran. 
                - Mendapatkan tiket digital.
    admin: - Membuat template form pendaftaran untuk tiap event. 
           - Menentukan field yang wajib diisi (misalnya NIK, kontak darurat). 
           - Verifikasi data pendaftar.
     
   ### 7. Riwayat dan sertifikat
    user biasa: - Melihat event yang sudah pernah diikuti
                - Melihat hasil lomba dan waktu finish
                - Mengunduh sertifikat elektronik (opsional)
     admin: - Menggenerate hasil lomba dan sertifikatnya
            - Mendedit data hasil lomba
     
   ### 8. Notifikasi dari sistem
     user biasa: - Menerima status pendagtaran dan update event
                 - Mendapat reminder sebelum lomba (opsional)
     admin: - Membuat dan mengirim notifikasi ke peserta event baik secara sistem atau email
  
   ### 9. Form pembuatan marathon dari user
      user biasa: - Mengisi Form Pengajuan Event yang disediakan admin.
                  - Isi form meliputi:
                  - Nama event
                  - Lokasi (alamat / titik koordinat peta)
                  - Checkpoint (bisa input manual / upload file GPS)
                  - Jarak lomba (misalnya 5K, 10K, 21K, 42K)
                  - Tanggal & waktu
                  - Deskripsi event
                  - Kuota peserta & biaya (opsional)
     admin: - Menerima pengajuan di dashboard.
            - Bisa review detail: apakah event valid, apakah sesuai syarat (misalnya izin, keamanan, sponsor).
            - Mengapprove atau menolak 




## 6. Tautan deployment PWS dan link design
### Link Deployment
  https://muhammad-rafi419-vacathon.pbp.cs.ui.ac.id/
### Link Design
  https://www.figma.com/design/wTbqvv5EY2yzpy6rWUxJxH/project-tengah-semester?m=auto&t=b8kVrqHCfToOhZYu-1
