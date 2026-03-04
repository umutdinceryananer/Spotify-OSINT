# Spotify-OSINT

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-OSINT-1DB954?logo=spotify&logoColor=white)

A Python service that watches public Spotify playlists for new track additions and sends you a Telegram notification the moment something gets added. Runs automatically every 30 minutes via GitHub Actions, costs nothing, and lives rent-free in your head — just like the person whose playlists you're watching.

---

## Architecture

```mermaid
flowchart LR
    A["⏰ GitHub Actions\n(every 30 min)"] --> B["🎵 Spotify API\n(snapshot check)"]
    B -->|changed| C["🌐 Playwright\n(scrape tracks)"]
    B -->|unchanged| X["💤 Skip"]
    C --> D["📝 Lrclib\n(fetch lyrics)"]
    D --> E["🤖 Groq LLM\n(emotional analysis)"]
    E --> F["📨 Telegram\n(notifications)"]
    C --> G["🗄️ Supabase\n(PostgreSQL)"]
    E --> G

    style A fill:#2088FF,color:#fff
    style B fill:#1DB954,color:#fff
    style C fill:#FF6B35,color:#fff
    style D fill:#9B59B6,color:#fff
    style E fill:#E74C3C,color:#fff
    style F fill:#0088CC,color:#fff
    style G fill:#3ECF8E,color:#fff
    style X fill:#95a5a6,color:#fff
```

---

## How it works

1. Fetches the playlist's `snapshot_id` from the Spotify API — a unique fingerprint that changes on any modification.
2. If the snapshot hasn't changed since the last run, it does nothing (no browser, no cost, no drama).
3. If it has changed, it launches a headless Chromium browser (Playwright) to scrape the new tracks from the Spotify web player — because Spotify removed public track access from their API in early 2026.
4. Sends a Telegram notification for each new track.
5. Fetches the track's lyrics from [Lrclib](https://lrclib.net) and sends them to Groq (llama-3.3-70b-versatile) for a short emotional analysis, delivered as a second Telegram message.
6. Saves everything to a Supabase (PostgreSQL) database.
7. **Weekly reports** (every Monday at 12:00 Istanbul time):
   - **Time analysis:** Detects when the playlist owner is most active — peak hours, time slot distribution (night/morning/afternoon/evening).
   - **Mood report:** Summarizes the emotional tone of all tracks added in the past 7 days based on accumulated individual analyses.

> **Timezone:** All time analysis uses Europe/Istanbul (UTC+3). Timestamps are stored in UTC and converted at report time.

---

## Prerequisites

- Python 3.12+
- A [Spotify Developer](https://developer.spotify.com/dashboard) app (free)
- A [Supabase](https://supabase.com) project (free tier is enough)
- A Telegram bot (via [@BotFather](https://t.me/BotFather))
- A [Groq](https://console.groq.com) API key (free)
- A GitHub account (for the automated workflow)

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/spotify-osint.git
cd spotify-osint
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Create a Spotify app

Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard), create an app, and note your **Client ID** and **Client Secret**.

### 4. Create a Telegram bot

Message [@BotFather](https://t.me/BotFather) on Telegram, create a new bot, and get your **bot token**. Then send any message to your bot and visit:

```
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

Find your **chat ID** in the response.

### 5. Set up Supabase

Create a project at [supabase.com](https://supabase.com). In the SQL editor, run `schema.sql`:

```sql
CREATE TABLE playlists (
    id          VARCHAR     PRIMARY KEY,
    name        VARCHAR     NOT NULL,
    owner_id    VARCHAR     NOT NULL,
    is_active   BOOLEAN     DEFAULT TRUE,
    added_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tracked_tracks (
    track_id    VARCHAR     NOT NULL,
    playlist_id VARCHAR     NOT NULL REFERENCES playlists(id),
    track_name  VARCHAR     NOT NULL,
    artist_names TEXT[]     NOT NULL,
    album_name  VARCHAR,
    spotify_url VARCHAR,
    added_at    TIMESTAMPTZ,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    analysis    TEXT,
    PRIMARY KEY (track_id, playlist_id)
);
```

Then run these migrations:

```sql
ALTER TABLE playlists ADD COLUMN snapshot_id TEXT;
ALTER TABLE tracked_tracks ADD COLUMN IF NOT EXISTS analysis TEXT;
```

Go to **Project Settings → Database** and copy the **Session Pooler** connection string (the one that looks like `postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres`). Do **not** use the direct connection string — it requires IPv6 and will fail on GitHub Actions.

### 6. Configure environment variables

```bash
cp .env.example .env
```

Fill in `.env`:

```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
DATABASE_URL=your_supabase_session_pooler_url
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
GROQ_API_KEY=your_groq_api_key
```

### 7. Add playlists to monitor

The playlist must be **public**. Grab the playlist ID from its Spotify URL (`open.spotify.com/playlist/<ID>`):

```bash
python -m scripts.manage_playlists add <playlist_id>
```

Other commands:

```bash
python -m scripts.manage_playlists list           # show all monitored playlists
python -m scripts.manage_playlists remove <id>    # stop monitoring a playlist
```

### 8. Run the monitor

```bash
python -m src.monitor
```

The first run scans every playlist in full to build a baseline — no notifications are sent. Subsequent runs only trigger when the snapshot changes.

---

## GitHub Actions (automated)

The workflow in `.github/workflows/monitor.yml` runs every 30 minutes automatically.

Add the following secrets to your GitHub repository under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `SPOTIFY_CLIENT_ID` | From your Spotify app |
| `SPOTIFY_CLIENT_SECRET` | From your Spotify app |
| `DATABASE_URL` | Supabase session pooler URL |
| `TELEGRAM_BOT_TOKEN` | From BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `GROQ_API_KEY` | From console.groq.com |

You can also trigger the workflow manually from the **Actions** tab.

---

## Ethical disclaimer

People frequently put themselves in situations where they feel compelled to watch what the other side will do next. In those moments, anxiety and paranoia push you toward calculating the probability of things that will never happen. I've caught myself doing that math more times than I'd like to admit.

If I had to draw an analogy, I think of those moments as a corridor, one with no entrance, no exit, and not even a door in sight. You can stand still in that corridor. Motionless, curled up, waiting for time to pass. I consider that a disservice one does to oneself. During this process, I chose as my north star a line by John Milton that is far more radical than anything I could articulate, and perhaps easier to understand: *"Better to reign in Hell, than to serve in Heaven."*

For a long time, in moments like these, I chose to stand still, contradicting my own nature. Maybe it was a defense mechanism, maybe an instinctive reflex. Then I found myself writing these lines of code with Claude, thinking: "If I can't leave this corridor for a while, I might as well make the most of it."

When I first encountered software, I thought it was a set of tasks that would earn me money and that I'd carry out for the rest of my life. The person who changed that perspective was my father. Among millions who cannot exist without consuming, he is one of those rare individuals who cannot exist without creating. After he suggested I approach software as a craft, I made my first open-source attempts. I certainly can't say I've mastered it, but I can say I've at least gained the freedom to choose what I want.

This repo is the product of time spent in that corridor. The answer to a question I kept asking myself: "Can I at least do something?"

Before saying goodbye, in keeping with the concept, let me squeeze in a song and leave you alone with the project.
[Çilekeş - Y.O.K.](https://www.youtube.com/watch?v=s9KTAxJGqks)

Take care.

---

---

# Spotify-OSINT

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![GitHub Actions](https://img.shields.io/badge/Automation-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-OSINT-1DB954?logo=spotify&logoColor=white)

Herkese açık Spotify playlistlerini izleyen ve yeni bir şarkı eklendiği anda sana Telegram bildirimi gönderen bir Python servisi. GitHub Actions üzerinden 30 dakikada bir otomatik çalışır, ücretsizdir ve Spotify peşime adam takmadığı sürece de çalışmaya devam edecek.

---

## Mimari

```mermaid
flowchart LR
    A["⏰ GitHub Actions\n(30 dk'da bir)"] --> B["🎵 Spotify API\n(snapshot kontrolü)"]
    B -->|değişti| C["🌐 Playwright\n(şarkı çekme)"]
    B -->|değişmedi| X["💤 Atla"]
    C --> D["📝 Lrclib\n(şarkı sözleri)"]
    D --> E["🤖 Groq LLM\n(duygusal analiz)"]
    E --> F["📨 Telegram\n(bildirimler)"]
    C --> G["🗄️ Supabase\n(PostgreSQL)"]
    E --> G

    style A fill:#2088FF,color:#fff
    style B fill:#1DB954,color:#fff
    style C fill:#FF6B35,color:#fff
    style D fill:#9B59B6,color:#fff
    style E fill:#E74C3C,color:#fff
    style F fill:#0088CC,color:#fff
    style G fill:#3ECF8E,color:#fff
    style X fill:#95a5a6,color:#fff
```

---

## Nasıl çalışır

1. Spotify API'den playlistin `snapshot_id`'sini çeker — herhangi bir değişiklikte değişen benzersiz bir parmak izi.
2. Snapshot son çalıştırmadan beri değişmemişse hiçbir şey yapmaz (tarayıcı açılmaz, işlem olmaz).
3. Değiştiyse headless Chromium tarayıcı (Playwright) açarak Spotify web playerdan yeni şarkıları çeker — Spotify 2026 başında herkese açık playlist erişimini API'den kaldırdığı için.
4. Her yeni şarkı için Telegram bildirimi gönderir.
5. [Lrclib](https://lrclib.net)'den şarkı sözlerini çekip Groq'a (llama-3.3-70b-versatile) göndererek kısa bir duygusal analiz üretir, ikinci bir Telegram mesajı olarak iletir.
6. Her şeyi Supabase (PostgreSQL) veritabanına kaydeder.
7. **Haftalık raporlar** (her Pazartesi 12:00 İstanbul saati):
   - **Saat analizi:** Playlist sahibinin en aktif olduğu saatleri tespit eder — zirve saatler, zaman dilimi dağılımı (gece/sabah/öğleden sonra/akşam).
   - **Ruh hali raporu:** Son 7 günde eklenen şarkıların biriken bireysel analizlerinden genel duygusal tonu özetler.

> **Timezone:** Tüm saat analizleri Europe/Istanbul (UTC+3) üzerinden yapılır. Zaman damgaları UTC olarak kaydedilir, rapor sırasında dönüştürülür.

---

## Gereksinimler

- Python 3.12+
- [Spotify Developer](https://developer.spotify.com/dashboard) uygulaması (ücretsiz)
- [Supabase](https://supabase.com) projesi (ücretsiz tier yeterli)
- Telegram botu ([@BotFather](https://t.me/BotFather) üzerinden)
- [Groq](https://console.groq.com) API key'i (ücretsiz)
- GitHub hesabı (otomatik çalıştırma için)

---

## Kurulum

### 1. Repoyu klonla

```bash
git clone https://github.com/kullanici-adin/spotify-osint.git
cd spotify-osint
```

### 2. Sanal ortam oluştur ve bağımlılıkları yükle

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 3. Spotify uygulaması oluştur

[developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) adresine gidip uygulama oluştur. **Client ID** ve **Client Secret**'ı not al.

### 4. Telegram botu oluştur

Telegram'da [@BotFather](https://t.me/BotFather)'a mesaj at, yeni bot oluştur, **bot token**'ını al. Sonra botuna herhangi bir mesaj gönder ve şu adrese git:

```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

Gelen yanıttaki **chat ID**'yi not al.

### 5. Supabase kurulumu

[supabase.com](https://supabase.com)'da proje oluştur. SQL editöründe `schema.sql`'i çalıştır:

```sql
CREATE TABLE playlists (
    id          VARCHAR     PRIMARY KEY,
    name        VARCHAR     NOT NULL,
    owner_id    VARCHAR     NOT NULL,
    is_active   BOOLEAN     DEFAULT TRUE,
    added_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tracked_tracks (
    track_id    VARCHAR     NOT NULL,
    playlist_id VARCHAR     NOT NULL REFERENCES playlists(id),
    track_name  VARCHAR     NOT NULL,
    artist_names TEXT[]     NOT NULL,
    album_name  VARCHAR,
    spotify_url VARCHAR,
    added_at    TIMESTAMPTZ,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    analysis    TEXT,
    PRIMARY KEY (track_id, playlist_id)
);
```

Ardından bu migration'ları çalıştır:

```sql
ALTER TABLE playlists ADD COLUMN snapshot_id TEXT;
ALTER TABLE tracked_tracks ADD COLUMN IF NOT EXISTS analysis TEXT;
```

**Project Settings → Database** kısmından **Session Pooler** bağlantı stringini kopyala (`postgresql://postgres.xxx:password@aws-0-region.pooler.supabase.com:5432/postgres` gibi görünen). Direkt bağlantı stringini kullanma — IPv6 gerektiriyor ve GitHub Actions'ta çalışmıyor.

### 6. Ortam değişkenlerini ayarla

```bash
cp .env.example .env
```

`.env` dosyasını doldur:

```
SPOTIFY_CLIENT_ID=spotify_client_id
SPOTIFY_CLIENT_SECRET=spotify_client_secret
DATABASE_URL=supabase_session_pooler_url
TELEGRAM_BOT_TOKEN=bot_token
TELEGRAM_CHAT_ID=chat_id
GROQ_API_KEY=groq_api_key
```

### 7. Takip edilecek playlistleri ekle

Playlist **herkese açık** olmalı. Playlist ID'sini Spotify URL'inden al (`open.spotify.com/playlist/<ID>`):

```bash
python -m scripts.manage_playlists add <playlist_id>
```

Diğer komutlar:

```bash
python -m scripts.manage_playlists list           # takip edilen playlistleri listele
python -m scripts.manage_playlists remove <id>    # takibi bırak
```

### 8. Monitörü çalıştır

```bash
python -m src.monitor
```

İlk çalıştırmada her playlist baştan taranarak baseline oluşturulur — bildirim gönderilmez. Sonraki çalıştırmalarda yalnızca snapshot değiştiğinde aksiyon alınır.

---

## GitHub Actions (otomatik)

`.github/workflows/monitor.yml` her 30 dakikada bir otomatik çalışır.

GitHub reposunda **Settings → Secrets and variables → Actions** altına şu secretları ekle:

| Secret | Değer |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify uygulamasından |
| `SPOTIFY_CLIENT_SECRET` | Spotify uygulamasından |
| `DATABASE_URL` | Supabase session pooler URL |
| `TELEGRAM_BOT_TOKEN` | BotFather'dan |
| `TELEGRAM_CHAT_ID` | Telegram chat ID'n |
| `GROQ_API_KEY` | console.groq.com'dan |

Workflow'u **Actions** sekmesinden manuel olarak da tetikleyebilirsin.

---

## Etik sorumluluk reddi

İnsan sıklıkla kendisini, karşı tarafın ne yapacağını izlemek mecburiyetinde hissedeceği durumlara sokar. Böyle zamanlarda vesvese ve kuruntu, kişiyi olmayacak şeylerin ihtimalini hesaplamaya iter.

Bu anları girişi, çıkışı ve hiç hatta kapısı bile bulunmayan bir koridor gibi değerlendiriyorum. Koridorda durabilirsiniz, hareketsiz, cenin pozisyonunda, zamanın geçmesini bekleyerek. Bana göre bu insanın kendisine yaptığı bir haksızlık. Milton'ın sözüyle: *"Cennette hizmet etmektense, cehennemde hükmetmeyi yeğlerim."*

Uzun süre ben de tam tersini yapıyordum. Savunma mekanizması mıydı, içgüdüsel bir refleks miydi, bilmiyorum. Sonra kendimi "madem çıkamıyorum, tadını çıkarayım" diyerek bu kodları yazarken buldum.

Yazılımla ilk tanıştığımda bunu para kazanmanın ve ömür boyu sürecek görevler bütününün aracı olarak görüyordum. Babam bana zanaat olarak yaklaşmayı öğretti. O, tüketmeden var olamayan milyonların arasında üretmeden var olamayan, eşine az rastlanan birisi. İlk açık kaynak denemelerimi onun etkisiyle yaptım.

Bu repo da o koridorda geçirilen vaktin ürünü. "En azından bir şeyler yapabilir miyim?" sorusunun cevabı.

Veda etmeden araya bir şarkı sıkıştırayım, konsept gereği.
[Çilekeş - Y.O.K.](https://www.youtube.com/watch?v=s9KTAxJGqks)

Kalın sağlıcakla.
