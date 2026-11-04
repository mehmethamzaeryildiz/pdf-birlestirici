# PDF Birleştirici & Sıralayıcı

Basit, hızlı ve kullanıcı dostu arayüze sahip, Python (Tkinter) ve `pypdf` kullanılarak geliştirilmiş masaüstü PDF birleştirme aracı.

---

## Özellikler

* **Kolay Sıralama:** Listeye eklenen PDF dosyalarının sırasını "Yukarı" ve "Aşağı" butonlarıyla değiştirebilirsiniz.
* **PDF Ayırma:** Listede seçili PDF'i parçalara ayırır. Seçenekler: sayfa aralıkları (`1-5, 6-10`), her sayfayı ayrı dosya, her N sayfada bir, belirli sayfaları çıkarma (`2, 7, 9-12`), boyuta göre (ör. en fazla 10 MB) ve yer imlerine (bookmark) göre.
* **Şifreli PDF Desteği:** Şifreli dosyalar için birleştirme, yazdırma ve ayırma sırasında şifre sorulur.
* **Güvenli Kayıt:** Çıktı, birleştirilen dosyalardan birinin üzerine yazılamaz; hata olursa hangi dosyada olduğu gösterilir.
* **RAM Koruması / Boyut Sınırı:** Toplam dosya boyutu 500 MB'ı aşan durumlarda sistemi korumak için uyarı verir.
* **Kolay Kullanım:** Python kurulumu gerektirmeyen (`.exe` sürümü ile) pratik masaüstü deneyimi.
* **Sade Arayüz:** Modern Tkinter tasarımı.

---


## 📥 İndir ve Kullan

Uygulamanın en son kararlı sürümünü bilgisayarınıza indirerek doğrudan çalıştırabilirsiniz:

1. [Releases Sayfası](https://github.com/mehmethamzaeryildiz/pdf-birlestirici/releases/latest) adresine gidin.
2. En son sürümün altındaki **`PDF_Birlestirici_Setup.exe`** dosyasını indirin.
3. Dosyaya çift tıklayıp kurulumu tamamlayın. Uygulama Başlat menüsüne (isteğe bağlı olarak masaüstüne) eklenir.

> **"Windows kişisel bilgisayarınızı korudu" uyarısı çıkarsa:** Uygulama dijital olarak imzalanmadığı için Windows SmartScreen bu uyarıyı gösterir. **"Ek bilgi" → "Yine de çalıştır"** diyerek kuruluma devam edebilirsiniz.
>
> Kaldırmak için: Ayarlar → Uygulamalar → PDF Birleştirici → Kaldır (veya Denetim Masası → Programlar ve Özellikler).

### macOS

1. Releases sayfasından Mac'inize uygun dosyayı indirin: **`PDF_Birlestirici-macOS-AppleSilicon.zip`** (M1/M2/M3/M4) veya **`PDF_Birlestirici-macOS-Intel.zip`** (Intel). Hangisi olduğunu  → Bu Mac Hakkında'dan görebilirsiniz.
2. Zip'i açın, **PDF Birlestirici** uygulamasını **Uygulamalar** klasörüne sürükleyin.
3. İlk açılışta "doğrulanamadı" uyarısı çıkarsa (uygulama Apple tarafından imzalanmadı): **Sistem Ayarları → Gizlilik ve Güvenlik** → en altta **"Yine de Aç"**. Alternatif: Terminal'de `xattr -cr "/Applications/PDF Birlestirici.app"`.

### Linux

`PDF_Birlestirici-Linux.tar.gz` dosyasını indirip açın, `PDF Birlestirici/PDF Birlestirici` dosyasını çalıştırın.

> macOS/Linux'ta yazdırma sistemin yazıcıları (CUPS) üzerinden yapılır; yazıcının sürücü ayar penceresi ("Ayarlar…") yalnızca Windows'ta vardır.

---

## 🛠 Kaynaktan Çalıştırma

Python 3.8+ gerekir.

```bash
pip install -r requirements.txt
python pdf_birlestirici.py
```

Test: `python test_birlestir.py` (çıktı `OK` olmalı)

macOS ve Linux paketleri GitHub Actions ile otomatik derlenir (`.github/workflows/build.yml`): Releases'ta bir sürüm yayınlandığında dosyalar o sürüme eklenir; Actions sekmesinden elle de çalıştırılabilir.

### Kurulum dosyası (setup) üretme

[Inno Setup 6](https://jrsoftware.org/isinfo.php) gerekir (`winget install JRSoftware.InnoSetup`).

```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --icon pdf_birlestirici.ico --name PDF_Birlestirici pdf_birlestirici.py
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" setup.iss
```

Çıktı: `Output\PDF_Birlestirici_Setup.exe`. Yeni sürümde `setup.iss` içindeki `AppVersion` değerini güncelleyin.

---
