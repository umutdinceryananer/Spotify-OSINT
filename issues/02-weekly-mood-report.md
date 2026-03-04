# Issue #02 — Haftalık Mood Raporu

## Amaç

Son 7 günde eklenen şarkıların bireysel analizlerini toplayıp, playlist sahibinin genel ruh halini özetleyen haftalık bir Telegram raporu üretmek.

## Motivasyon

- Tek tek şarkı analizleri anlık bilgi veriyor ama büyük resmi göstermiyor
- Haftalık özet, kişinin duygusal eğilimini zaman içinde takip etmeyi sağlıyor
- Tweet malzemesi: "Bu hafta playlist sahibi melankolik bir dönemden geçiyor, 5 şarkının 4'ü ayrılık temalı"

## Ön Gereksinimler

- **Analiz metinlerini DB'ye kaydet:** Şu an `groq_client.analyze_track()` sonuçları sadece Telegram'a gönderiliyor, DB'ye yazılmıyor. Haftalık rapor için bu analizlerin birikmiş olması lazım
  - `tracked_tracks` tablosuna `analysis TEXT` kolonu ekle (migration)
  - `monitor.py`'deki akışta analizi DB'ye de kaydet
  - `schema.sql`'i güncelle

## Kapsam

### Commit 1: DB migration + analiz kaydetme
- `tracked_tracks` tablosuna `analysis TEXT` kolonu ekle
- `database.py`'ye `update_track_analysis(track_id, playlist_id, analysis)` ekle
- `monitor.py`'de `analyze_track()` sonucunu DB'ye kaydet
- `schema.sql`'i güncelle

### Commit 2: Haftalık mood özeti oluşturma
- `database.py`'ye `get_analyses_for_report(playlist_id, days=7)` ekle — son 7 gündeki analizleri döndürür
- `src/report.py`'ye `generate_mood_report()` ekle — biriken analizleri Groq'a toplu gönderip haftalık ruh hali özeti üret
- Issue #01'deki saat analizini de mood raporunun içine entegre et (tek mesaj)

### Commit 3: Telegram bildirimi + workflow güncelleme
- `telegram.py`'ye `send_weekly_report_notification()` ekle — saat analizi + mood özeti tek mesajda
- `weekly_report.yml` workflow'unu güncelle

## Timezone

- Europe/Istanbul (UTC+3) — Issue #01 ile aynı

## Doğrulama

- DB'de biriken analizlerle `python -m src.report` çalıştır
- Telegram'a mood özeti + saat analizi içeren tek rapor mesajı geldiğini kontrol et

## Kapsam Dışı

- README güzelleştirme (Issue #03)
