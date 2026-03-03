# Roadmap — stalkify-but-legal

> Mimari kararlar: Python · GitHub Actions (cron) · Supabase (PostgreSQL) · Telegram Bot API · Spotify Client Credentials

---

## Issue 1: Environment and Authentication Setup
**Status:** OPEN

### Description
Projenin çalışması için gereken tüm harici servislerin (Spotify, Supabase, Telegram) kurulumunu yapmak ve Python proje iskeletini oluşturmak.

### Tasks

**Spotify:**
- [ ] [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)'da yeni bir uygulama oluştur.
- [ ] **Client ID** ve **Client Secret** değerlerini al.
- [ ] Authentication method olarak **Client Credentials** seç (OAuth2/kullanıcı girişi gerekmez — yalnızca public playlist takibi yapılacak).

**Supabase:**
- [ ] [Supabase](https://supabase.com)'de yeni bir proje oluştur.
- [ ] `Settings > Database` altından **Connection String** (URI) değerini al.
- [ ] Aşağıdaki şemayı çalıştır:
  ```sql
  CREATE TABLE playlists (
      id VARCHAR PRIMARY KEY,         -- Spotify playlist ID
      name VARCHAR NOT NULL,
      owner_id VARCHAR NOT NULL,
      is_active BOOLEAN DEFAULT TRUE,
      added_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE TABLE tracked_tracks (
      track_id VARCHAR NOT NULL,
      playlist_id VARCHAR NOT NULL REFERENCES playlists(id),
      track_name VARCHAR NOT NULL,
      artist_names TEXT[] NOT NULL,
      album_name VARCHAR,
      spotify_url VARCHAR,
      added_at TIMESTAMPTZ,           -- Playlist'e eklenme zamanı (Spotify verisi)
      detected_at TIMESTAMPTZ DEFAULT NOW(),  -- Bizim tespit ettiğimiz zaman
      PRIMARY KEY (track_id, playlist_id)
  );
  ```

**Telegram:**
- [ ] Telegram'da `@BotFather` ile yeni bir bot oluştur, **Bot Token** değerini al.
- [ ] Bildirimlerin gönderileceği chat'in **Chat ID** değerini al (`@userinfobot` ile).

**Python Projesi:**
- [ ] Proje klasör yapısını oluştur:
  ```
  stalkify-but-legal/
  ├── .github/
  │   └── workflows/
  │       └── monitor.yml
  ├── src/
  │   ├── __init__.py
  │   ├── config.py       # Env variable yönetimi
  │   ├── spotify.py      # Spotify API client
  │   ├── database.py     # Supabase/PostgreSQL işlemleri
  │   ├── telegram.py     # Telegram bildirim modülü
  │   └── monitor.py      # Ana orkestrasyon mantığı
  ├── scripts/
  │   └── manage_playlists.py  # Playlist ekle/çıkar CLI
  ├── requirements.txt
  └── .env.example
  ```
- [ ] `requirements.txt` dosyasını oluştur.
- [ ] `.env.example` dosyasını oluştur.
- [ ] `src/config.py` modülünü yaz (env variable doğrulama ile).
- [ ] `src/spotify.py` içinde Client Credentials auth akışını yaz.
- [ ] Bağlantı testini yaz (`python -m src.spotify` ile çalışabilir).

**GitHub Actions:**
- [ ] Repository `Settings > Secrets and variables > Actions` altına şu secret'ları ekle:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `DATABASE_URL`
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
- [ ] `.github/workflows/monitor.yml` iskeletini oluştur.

### Technical Details
- **Auth Method:** Client Credentials Flow — kullanıcı etkileşimi gerektirmez, yalnızca `client_id` + `client_secret` ile token alınır.
- **Token Endpoint:** `POST https://accounts.spotify.com/api/token` (`grant_type=client_credentials`)
- **Token Süresi:** 3600 saniye — her GitHub Actions run'ında yeni token alınır, saklamaya gerek yok.
- **Scope:** Gerekmez — public endpoint'ler için scope zorunlu değil.
- **Private Playlist Davranışı:** API 403 döndürürse playlist sessizce atlanır, hata fırlatılmaz.

### Definition of Done
- `python -m src.spotify` komutu Spotify API'dan geçerli bir access token alıyor.
- Supabase bağlantısı sağlanıyor ve tablolar oluşturulmuş durumda.
- Telegram botuna test mesajı gönderilebiliyor.
- GitHub Actions workflow manuel tetiklendiğinde (`workflow_dispatch`) başarıyla çalışıyor.

---

## Issue 2: Spotify API Data Retrieval Implementation
**Status:** OPEN

### Description
`src/spotify.py` modülünü genişleterek takip edilen playlist'lerden tüm şarkı verilerini çeken ve yapılandırılmış Python nesnelerine dönüştüren bir client yazmak.

### Tasks
- [ ] `Track` dataclass'ını tanımla:
  - `track_id`, `track_name`, `artist_names`, `album_name`, `spotify_url`, `added_at`
- [ ] `get_playlist_tracks(playlist_id: str) -> list[Track]` fonksiyonunu yaz.
- [ ] 100'den fazla şarkı içeren playlist'ler için `offset` tabanlı pagination'ı implement et.
- [ ] `fields` query parametresi ile payload boyutunu küçült.
- [ ] Private/silinmiş playlist'ler için 403/404 response'larını yakala, `None` ya da boş liste döndür (crash yok).
- [ ] Supabase'deki `playlists` tablosundan aktif playlist ID'lerini çeken `get_active_playlists() -> list[str]` fonksiyonunu `src/database.py`'a ekle.

### Technical Details
- **Endpoint:** `GET https://api.spotify.com/v1/playlists/{playlist_id}/tracks`
- **Fields Filter:** `items(added_at,track(id,name,artists(name),album(name),external_urls))`
- **Pagination:** `limit=100&offset={n}` — response'daki `next` alanı `None` olana kadar devam et.
- **Rate Limit:** Spotify, Client Credentials için agresif rate limit uygulamaz; 6 playlist için sorun yaşanmaz.

### Definition of Done
- 100+ şarkılı bir playlist'in tüm şarkıları eksiksiz çekilebiliyor.
- Private/silinmiş playlist istekleri uygulamayı çökertmiyor.
- Çıktı, tip güvenli `Track` nesnelerinden oluşan bir liste.

---

## Issue 3: Data Persistence and State Management
**Status:** OPEN

### Description
`src/database.py` modülünü yazarak Supabase üzerindeki PostgreSQL instance'ı ile tüm okuma/yazma işlemlerini yönetmek.

### Tasks
- [ ] `psycopg2` veya `asyncpg` ile bağlantı yönetimini implement et (connection pooling dahil).
- [ ] `get_known_track_ids(playlist_id: str) -> set[str]` fonksiyonunu yaz.
- [ ] `save_new_tracks(tracks: list[Track], playlist_id: str) -> None` fonksiyonunu yaz.
  - `INSERT ... ON CONFLICT DO NOTHING` ile upsert mantığı kullan.
- [ ] `get_active_playlists() -> list[dict]` fonksiyonunu yaz.
- [ ] İlk çalıştırma senaryosunu ele al: Tablo boşsa tüm mevcut şarkılar "bilinen" olarak işaretle, bildirim gönderme.

### Technical Details
- **Bağlantı:** `DATABASE_URL` environment variable (Supabase connection string).
- **Upsert Stratejisi:** `ON CONFLICT (track_id, playlist_id) DO NOTHING` — tekrar bildirim gönderilmesini engeller.
- **İlk Çalıştırma Tespiti:** `tracked_tracks` tablosu ilgili `playlist_id` için boşsa → mevcut tüm şarkıları kaydet, bildirim gönderme.

### Definition of Done
- Bilinen track ID'leri doğru şekilde alınıyor ve set olarak dönüyor.
- Yeni şarkılar veritabanına kaydediliyor, aynı şarkı için duplicate kayıt oluşmuyor.
- İlk çalıştırmada bildirim gönderilmiyor.

---

## Issue 4: New Song Detection Logic
**Status:** OPEN

### Description
`src/monitor.py` içinde her playlist için Spotify'dan gelen güncel veriyi veritabanındaki bilinen şarkılarla karşılaştıran ve yeni eklemeleri tespit eden ana mantığı yazmak.

### Tasks
- [ ] Ana orkestrasyon döngüsünü yaz:
  1. Aktif playlist'leri DB'den çek.
  2. Her playlist için Spotify'dan güncel şarkı listesini çek.
  3. Bilinen ID'leri DB'den çek (`set`).
  4. Farkı hesapla: `new_tracks = [t for t in current if t.track_id not in known_ids]`.
  5. Yeni şarkı varsa bildirim gönder (Issue 5).
  6. Yeni şarkıları DB'ye kaydet.
- [ ] Private olan playlist atlandığında (boş liste döndüğünde) log bas, devam et.
- [ ] İlk çalıştırma senaryosunu `database.py`'dan gelen sinyal ile yönet.

### Technical Details
- **Karşılaştırma Anahtarı:** `track_id` (Spotify'ın unique şarkı ID'si).
- **Veri Yapısı:** Set farkı O(1) lookup ile — büyük playlist'lerde dahi performanslı.
- **Yan Etki Sırası:** Önce bildirim, sonra DB'ye kayıt — kayıt başarısız olursa duplicate bildirim riski yoktur.

### Definition of Done
- Yalnızca bir önceki çalışmadan bu yana eklenen şarkılar tespit ediliyor.
- Aynı şarkı için birden fazla bildirim gönderilmiyor.
- Private playlist atlatılıyor, uygulama çalışmaya devam ediyor.

---

## Issue 5: Notification Channel Integration
**Status:** OPEN

### Description
`src/telegram.py` modülünü yazarak yeni şarkı tespitinde Telegram Bot API üzerinden biçimli bildirim göndermek.

### Tasks
- [ ] `send_new_track_notification(track: Track, playlist_name: str) -> None` fonksiyonunu yaz.
- [ ] Telegram Markdown (MarkdownV2) ile mesaj şablonunu tasarla:
  ```
  🎵 Yeni şarkı eklendi!

  *{track_name}*
  👤 {artist_names}
  💿 {album_name}
  📋 Playlist: {playlist_name}

  🔗 [Spotify'da aç]({spotify_url})
  ```
- [ ] `send_error_notification(error_message: str) -> None` fonksiyonunu yaz (sistem hataları için).
- [ ] Yeni şarkı yoksa bildirim gönderme (boş mesaj engeli).
- [ ] Birden fazla yeni şarkı varsa her biri için ayrı mesaj gönder.

### Technical Details
- **API Endpoint:** `POST https://api.telegram.org/bot{token}/sendMessage`
- **Payload:** `chat_id`, `text`, `parse_mode=MarkdownV2`
- **Rate Limit:** Telegram, tek bir chat'e saniyede 1 mesaj sınırı uygular — çok şarkı varsa mesajlar arasına `time.sleep(1)` ekle.

### Definition of Done
- Test mesajı Telegram'da başarıyla alınıyor.
- Mesaj şablonu doğru biçimde görüntüleniyor (bold, link çalışıyor).
- Yeni şarkı olmadığında bildirim gönderilmiyor.

---

## Issue 6: Error Handling and Resilience
**Status:** OPEN

### Description
Spotify API rate limit'leri, ağ zaman aşımları ve bağlantı hatalarına karşı uygulamayı dayanıklı hale getirmek.

### Tasks
- [ ] Spotify API çağrıları için `tenacity` ile retry mekanizması ekle:
  - Max retry: 3
  - Bekleme: exponential backoff (1s, 2s, 4s)
  - Retry koşulları: `requests.exceptions.Timeout`, `requests.exceptions.ConnectionError`, HTTP 429, HTTP 5xx
- [ ] HTTP 429 response'undaki `Retry-After` header'ını oku ve o kadar bekle.
- [ ] Supabase bağlantı hatalarını yakala, Telegram'a sistem hatası bildirimi gönder.
- [ ] Her çalışma için structured logging ekle (`logging` modülü, JSON format).
- [ ] Beklenmedik exception'lar `monitor.py`'ın en üstünde yakalanarak Telegram'a iletilsin, GitHub Actions run'ı başarısız sayılmasın.

### Technical Details
- **Retry Kütüphanesi:** `tenacity`
- **Loglama:** `logging` (JSON formatter) — GitHub Actions log'larında aranabilir olması için.
- **Hata Bildirimi:** `send_error_notification()` fonksiyonu (Issue 5'te tanımlı).

### Definition of Done
- Geçici ağ hataları uygulamayı crash ettirmiyor.
- HTTP 429 alındığında `Retry-After` süresi kadar bekleniyor.
- Kalıcı hatalarda Telegram'a bildirim gönderiliyor.
- GitHub Actions log'larında hatalar structured formatta görünüyor.

---

## Issue 7: Scheduling and Production Deployment
**Status:** OPEN

### Description
GitHub Actions cron workflow'unu production'a almak ve otomatik çalışma döngüsünü aktif etmek.

### Tasks
- [ ] `.github/workflows/monitor.yml` dosyasını tamamla:
  - `schedule: cron: '*/30 * * * *'` (her 30 dakika)
  - `workflow_dispatch` (manuel tetikleme — test için)
  - `python-version: '3.12'`
  - Dependency caching (`actions/cache` ile `pip` cache)
- [ ] Tüm environment secret'larının workflow'da doğru eşleştirildiğini doğrula.
- [ ] İlk production run'ı manuel tetikle ve log'ları incele.
- [ ] Rate limit hesabı: 6 playlist × ~1 API çağrısı = günde 48 çalışmada toplam ~288 istek — Spotify limitleri içinde.
- [ ] `scripts/manage_playlists.py` CLI'ını tamamla:
  - `add <playlist_id>` — playlists tablosuna ekle
  - `remove <playlist_id>` — is_active = FALSE yap
  - `list` — aktif playlist'leri listele

### Technical Details
- **Cron Sıklığı:** Her 30 dakika (`*/30 * * * *`). GitHub Actions'ta cron'lar yoğun saatlerde birkaç dakika gecikebilir — bu proje için kabul edilebilir.
- **Ücretsiz Limit:** GitHub Actions free tier 2.000 dakika/ay → 30 dk'da bir çalışan job ~720 dakika/ay kullanır.
- **Dependency Cache:** `pip` bağımlılıkları cache'lenmeli, run süresi düşürülmeli.

### Definition of Done
- Workflow her 30 dakikada bir otomatik tetikleniyor.
- GitHub Actions log'larında başarılı çalışmalar görünüyor.
- `manage_playlists.py` ile CLI üzerinden playlist eklenip çıkarılabiliyor.

---

## Issue 8: Documentation and Maintenance
**Status:** OPEN

### Description
Projeyi sıfırdan kuracak biri için yeterli dokümantasyonu oluşturmak.

### Tasks
- [ ] `README.md` yaz:
  - Projenin ne yaptığını açıkla.
  - Gereksinimler (Python 3.12+, Supabase hesabı, Spotify Developer hesabı, Telegram botu).
  - Adım adım kurulum talimatları.
  - Tüm environment variable'ların listesi ve açıklamaları.
  - Playlist ekleme/çıkarma talimatları (`manage_playlists.py` kullanımı).
  - Troubleshooting bölümü (yaygın hatalar ve çözümleri).
- [ ] `.env.example` dosyasının güncel ve eksiksiz olduğunu doğrula.
- [ ] Supabase şemasını `schema.sql` olarak repository'ye ekle.

### Technical Details
- **Dokümantasyon Formatı:** Markdown.
- **Bakım:** Spotify API değişikliklerini takip et (changelog: [developer.spotify.com](https://developer.spotify.com/documentation/web-api/)).

### Definition of Done
- `README.md` tamamlanmış ve kurulum adımları eksiksiz.
- `schema.sql` mevcut ve doğrudan Supabase SQL editor'da çalıştırılabilir.
- Başka bir geliştirici yalnızca `README.md`'ye bakarak projeyi ayağa kaldırabilir.

---

## Issue 9: Open Source LLM Provider Setup (Groq)
**Status:** OPEN

### Description
Python uygulamasını Groq API ile entegre ederek şarkı analizi için bir LLM bağlantısı kurmak.

### Tasks
- [ ] [Groq](https://console.groq.com)'da hesap aç ve **API Key** al (ücretsiz tier yeterli).
- [ ] `groq` Python SDK'yı `requirements.txt`'e ekle.
- [ ] `src/llm.py` modülünü oluştur:
  - `GroqClient` sınıfı (`api_key` ile init).
  - `analyze_track(track_name: str, artist: str) -> str` metodu — şarkı hakkında 1-2 cümlelik Türkçe özet döndürür.
- [ ] Model parametrelerini yapılandır: `model="llama-3.1-8b-instant"`, `temperature=0.3`, `max_tokens=150`.
- [ ] `GROQ_API_KEY` değerini GitHub Actions secret'larına ekle.
- [ ] Basit bir test yaz: Bilinen bir şarkı için anlamlı çıktı üretiliyor mu?

### Technical Details
- **Provider:** Groq (cloud-hosted, OpenAI-compatible API).
- **Model:** `llama-3.1-8b-instant` — hızlı ve ücretsiz tier'da cömert limit.
- **Groq Free Tier:** Dakikada 30 istek, günde 14.400 istek — bu proje için fazlasıyla yeterli.
- **Entegrasyon Noktası:** Issue 10'daki agentic analiz modülü bu client'ı kullanacak.

### Definition of Done
- `analyze_track("Bohemian Rhapsody", "Queen")` çağrısı anlamlı bir Türkçe metin döndürüyor.
- API key GitHub Actions secret'larına eklenmiş ve workflow'da erişilebilir durumda.

---

## Issue 10: Agentic Semantic Analysis Logic
**Status:** OPEN

### Description
Yeni tespit edilen şarkı hakkında Genius API (ya da web search) üzerinden veri toplayıp Groq LLM ile Türkçe bir özet üreten agentic mantığı `src/llm.py` içine yazmak.

### Tasks
- [ ] Genius API entegrasyonu:
  - [Genius Developer](https://genius.com/api-clients)'da uygulama oluştur, **Access Token** al.
  - `search_genius(track_name: str, artist: str) -> str | None` fonksiyonunu yaz — şarkının Genius URL'ini döndürür.
  - Genius sayfasından şarkı arka planı/annotation metnini parse et (`requests` + `BeautifulSoup`).
- [ ] `analyze_track` fonksiyonuna agentic akış ekle:
  1. Genius'ta şarkıyı ara.
  2. Bulunursa arka plan metnini çek, LLM prompt'una ekle.
  3. Bulunmazsa yalnızca şarkı adı ve sanatçıyla devam et.
  4. Groq'a Türkçe özet ürettir.
- [ ] System prompt'u mühendislik et:
  ```
  Sen bir müzik analisti asistanısın. Sana bir şarkının adı, sanatçısı ve
  varsa arka plan bilgisi verilecek. Bu şarkının teması, duygu tonu ve
  kültürel bağlamı hakkında Türkçe olarak 1-2 cümlelik özlü bir yorum yap.
  Yorum doğal ve samimi olsun.
  ```
- [ ] Zaman aşımı ekle: LLM 15 saniyede yanıt vermezse analiz atlanır, bildirim analizsiz gönderilir.
- [ ] Üretilen özeti Telegram mesaj şablonuna (Issue 5) entegre et.

### Technical Details
- **Genius API:** `GET https://api.genius.com/search?q={track}+{artist}` → ilk sonucun URL'i alınır.
- **Web Scraping:** BeautifulSoup ile `<div data-lyrics-container>` ya da annotation alanları parse edilir.
- **Fallback:** Genius'ta bulunamazsa LLM yalnızca şarkı adı + sanatçıyla çalışır.
- **Timeout:** `requests` timeout=10s, Groq API timeout=15s.

### Definition of Done
- Yeni şarkı bildirimlerinde Türkçe analiz metni görünüyor.
- Genius'ta bulunamayan şarkılar için fallback çalışıyor, bildirim yine gönderiliyor.
- Analiz süreci 15 saniyeyi aşmıyor.
