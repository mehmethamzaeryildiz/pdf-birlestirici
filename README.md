# PDF Birleştirici & Sıralayıcı

Basit, hızlı ve kullanıcı dostu arayüze sahip, Python (Tkinter) ve `pypdf` kullanılarak geliştirilmiş masaüstü PDF birleştirme aracı.

---

## Özellikler

* **Kolay Sıralama:** Listeye eklenen PDF dosyalarının sırasını "Yukarı" ve "Aşağı" butonlarıyla değiştirebilirsiniz.
* **Şifreli PDF Desteği:** Şifreli dosyalar için birleştirme sırasında şifre sorulur.
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
> Kaldırmak için: Ayarlar → Uygulamalar → PDF Birleştirici → Kaldır.

---

## 🛠 Kaynaktan Çalıştırma

Python 3.8+ gerekir.

```bash
pip install -r requirements.txt
python pdf_birlestirici.py
```

Test: `python test_birlestir.py` (çıktı `OK` olmalı)

### Kurulum dosyası (setup) üretme

[Inno Setup 6](https://jrsoftware.org/isinfo.php) gerekir (`winget install JRSoftware.InnoSetup`).

```bash
pip install pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --name PDF_Birlestirici pdf_birlestirici.py
"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" setup.iss
```

Çıktı: `Output\PDF_Birlestirici_Setup.exe`. Yeni sürümde `setup.iss` içindeki `AppVersion` değerini güncelleyin.

---
