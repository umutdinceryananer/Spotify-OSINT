# Issue #03 — README Güzelleştirme

## Amaç

GitHub'dan gelen trafiği dönüştürmek için README'yi görsel olarak zenginleştirmek. Twitter paylaşımından sonra repo'ya tıklayan kişilerin "wow" demesi lazım.

## Motivasyon

- Twitter'da viral olduktan sonra trafik direkt README'ye düşecek
- Şu anki README işlevsel ama görsel olarak sıradan
- Güzel bir README, star ve fork sayısını doğrudan etkiliyor

## Kapsam

### Telegram screenshot mockup'ları
- Gerçek Telegram bildirimlerinin screenshot'larını README'ye ekle:
  - Yeni şarkı bildirimi
  - Duygusal analiz mesajı
  - Haftalık saat analizi raporu (Issue #01)
  - Haftalık mood raporu (Issue #02, tamamlandıysa)
- `assets/` klasörü oluştur, görselleri oraya koy

### Mimari diyagram
- Basit bir akış diyagramı: Spotify API → Playwright → Lrclib → Groq → Telegram
- Mermaid veya ASCII art olabilir

### README içerik güncellemeleri
- Timezone bilgisi ekle (Issue #01'den not: Europe/Istanbul UTC+3)
- Lrclib entegrasyonunu vurgula (Genius'tan geçiş hikayesi kısa bir satırla)
- "How it works" bölümüne saat analizi + mood raporu adımlarını ekle
- Badge'ler ekle (Python version, License, GitHub Actions status)

### Provoke edici ethical disclaimer
- Mevcut disclaimer'ı daha dikkat çekici yaz
- "Is it weird?" sorusunu daha cesur bir tonla ele al

## Ön Gereksinimler

- Issue #01 tamamlanmış olmalı (saat analizi screenshot'ı için)
- Issue #02 tercihen tamamlanmış olmalı (mood raporu screenshot'ı için)

## Doğrulama

- README'yi GitHub'da preview et
- Görsellerin düzgün render edildiğini kontrol et
- Mobile view'da da iyi göründüğünden emin ol
