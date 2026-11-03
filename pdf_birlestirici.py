import io
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import sv_ttk
import pypdfium2 as pdfium
import win32con
import win32gui
import win32print
from pypdf import PdfReader, PdfWriter

MAX_BOYUT_MB = 500  # Maksimum toplam dosya boyutu sınırı (RAM koruması)


def _norm(yol):
    return os.path.normcase(os.path.abspath(yol))


def birlestir(dosyalar, kayit_yeri, sifre_sor):
    """PDF'leri sırayla kayit_yeri'ne yazar.

    sifre_sor(dosya_adi) -> str | None; None = kullanıcı iptal etti.
    Başarılıysa True, iptal edildiyse False döner. Hata mesajı dosya adını içerir.
    """
    if _norm(kayit_yeri) in {_norm(d) for d in dosyalar}:
        raise ValueError("Çıktı dosyası, birleştirilecek dosyalardan biri olamaz.\nLütfen farklı bir ad seçin.")

    toplam_mb = 0
    for dosya in dosyalar:
        try:
            toplam_mb += os.path.getsize(dosya) / (1024 * 1024)
        except OSError:
            raise ValueError(f"Dosya bulunamadı veya okunamıyor:\n{dosya}")
    if toplam_mb > MAX_BOYUT_MB:
        raise ValueError(
            f"Seçilen dosyaların toplam boyutu ({toplam_mb:.1f} MB),\n"
            f"izin verilen maksimum {MAX_BOYUT_MB} MB sınırını aşıyor.\n"
            f"Lütfen daha az veya daha küçük dosyalar seçin."
        )

    with PdfWriter() as merger:
        for dosya in dosyalar:
            try:
                reader = PdfReader(dosya)
                # Sadece sahip şifresi olan dosyalar boş şifreyle açılır
                if reader.is_encrypted and not reader.decrypt(""):
                    sifre = sifre_sor(os.path.basename(dosya))
                    if sifre is None:
                        return False
                    if not reader.decrypt(sifre):
                        raise ValueError("Şifre yanlış.")
                merger.append(reader)
            except Exception as e:
                raise RuntimeError(f"{os.path.basename(dosya)}:\n{e}") from e

        with open(kayit_yeri, "wb") as cikis_dosyasi:
            merger.write(cikis_dosyasi)
    return True


# ---------------- Ayırma ----------------

def sayfa_araliklari(metin, sayfa_sayisi):
    """'1-5, 8, 10-12' -> [(0, 4), (7, 7), (9, 11)]  (0 tabanlı, uçlar dahil)."""
    araliklar = []
    for parca in metin.replace(";", ",").split(","):
        parca = parca.strip()
        if not parca:
            continue
        bas, _, son = parca.partition("-")
        try:
            bas, son = int(bas), int(son or bas)
        except ValueError:
            raise ValueError(f"Geçersiz sayfa ifadesi: '{parca}'\nÖrnek: 1-5, 8, 10-12")
        if not 1 <= bas <= son <= sayfa_sayisi:
            raise ValueError(f"'{parca}' geçersiz.\nSayfalar 1 ile {sayfa_sayisi} arasında olmalı, "
                             f"aralık küçükten büyüğe yazılmalı.")
        araliklar.append((bas - 1, son - 1))
    if not araliklar:
        raise ValueError("Lütfen en az bir sayfa ya da aralık girin.\nÖrnek: 1-5, 8, 10-12")
    return araliklar


def _guvenli_ad(metin):
    return re.sub(r'[\\/:*?"<>|\r\n\t]', "_", metin).strip(" .")[:60] or "bolum"


def _pdf_boyutu(reader, sayfalar):
    with PdfWriter() as w:
        for i in sayfalar:
            w.add_page(reader.pages[i])
        tampon = io.BytesIO()
        w.write(tampon)
        return tampon.tell()


def _parcalar(reader, mod, deger, ad):
    """[(dosya adı, sayfa indeksleri)]"""
    n = len(reader.pages)
    if mod == "aralik":
        return [(f"{ad}_s{b + 1}" + (f"-{s + 1}" if s > b else ""), range(b, s + 1))
                for b, s in sayfa_araliklari(deger, n)]
    if mod in ("tek", "n"):
        adim = 1 if mod == "tek" else deger
        return [(f"{ad}_{i // adim + 1}", range(i, min(i + adim, n))) for i in range(0, n, adim)]
    if mod == "sec":
        return [(f"{ad}_secilen", [i for b, s in sayfa_araliklari(deger, n) for i in range(b, s + 1)])]
    if mod == "boyut":
        # ponytail: her sayfa eklenince parça baştan yazılıp ölçülür (O(n²)); paylaşılan font/resimler
        # yüzünden sayfa boyutları toplanamaz. Çok büyük belgede yavaşlarsa ikili aramaya geç.
        limit = deger * 1024 * 1024
        gruplar, grup = [], []
        for i in range(n):
            if grup and _pdf_boyutu(reader, grup + [i]) > limit:
                gruplar.append(grup)
                grup = []
            grup.append(i)
        gruplar.append(grup)
        return [(f"{ad}_{k + 1}", g) for k, g in enumerate(gruplar)]
    if mod == "yerimi":
        baslar = []
        for oge in reader.outline:
            if isinstance(oge, list):  # alt seviye yer imleri
                continue
            try:
                sayfa = reader.get_destination_page_number(oge)
            except Exception:
                continue
            if sayfa is not None and sayfa >= 0:
                baslar.append((sayfa, oge.title or ""))
        if not baslar:
            raise ValueError("Bu PDF'te yer imi (bookmark) bulunmuyor.\nBaşka bir ayırma yöntemi seçin.")
        baslar.sort(key=lambda b: b[0])
        parcalar = []
        for k, (sayfa, baslik) in enumerate(baslar):
            bas = 0 if k == 0 else sayfa  # ilk yer iminden önceki sayfalar ilk parçaya
            son = baslar[k + 1][0] if k + 1 < len(baslar) else n
            if son > bas:  # aynı sayfadaki yer imlerinden sonuncusu kalır
                parcalar.append((f"{ad}_{len(parcalar) + 1:02d}_{_guvenli_ad(baslik)}", range(bas, son)))
        return parcalar
    raise ValueError(f"Bilinmeyen ayırma modu: {mod}")


def ayir(dosya, mod, deger, klasor, sifre_sor, uzerine_yaz_sor=lambda yollar: True):
    """PDF'i parçalara ayırıp klasor'e yazar.

    mod: aralik ("1-5, 6-10"), tek, n (sayfa sayısı), sec ("2, 7, 9-12"), boyut (MB), yerimi.
    uzerine_yaz_sor(mevcut_yollar) -> bool; zaten var olan dosyalar için.
    Yazılan dosya yollarını, şifre ya da üzerine yazma sorusu iptal edildiyse None döner.
    """
    if _mb(dosya) > MAX_BOYUT_MB:
        raise ValueError(f"Dosya {MAX_BOYUT_MB} MB sınırını aşıyor.")
    try:
        reader = PdfReader(dosya)
        if reader.is_encrypted and not reader.decrypt(""):
            sifre = sifre_sor(os.path.basename(dosya))
            if sifre is None:
                return None
            if not reader.decrypt(sifre):
                raise ValueError("Şifre yanlış.")
    except Exception as e:
        raise RuntimeError(f"{os.path.basename(dosya)}:\n{e}") from e

    ad = os.path.splitext(os.path.basename(dosya))[0]
    parcalar = [(os.path.join(klasor, f"{isim}.pdf"), sayfalar)
                for isim, sayfalar in _parcalar(reader, mod, deger, ad)]
    yollar = [y for y, _ in parcalar]
    if _norm(dosya) in {_norm(y) for y in yollar}:
        raise ValueError("Parçalardan biri ayrılan dosyanın üzerine yazılacaktı.\nFarklı bir klasör seçin.")
    mevcut = [y for y in yollar if os.path.exists(y)]
    if mevcut and not uzerine_yaz_sor(mevcut):
        return None

    os.makedirs(klasor, exist_ok=True)
    for yol, sayfalar in parcalar:
        with PdfWriter() as w:
            for i in sayfalar:
                w.add_page(reader.pages[i])
            w.write(yol)
    return yollar


# ---------------- Yazdırma ----------------

ONCELIKLI_KAGITLAR = ("A4", "A3", "A5", "Letter", "Legal")


def yazicilar():
    """(yazıcı adları, varsayılan yazıcı)"""
    adlar = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
    try:
        varsayilan = win32print.GetDefaultPrinter()
    except Exception:
        varsayilan = adlar[0] if adlar else ""
    return adlar, varsayilan


def kagitlar(yazici):
    """{kağıt adı: kağıt kodu}; yaygın boyutlar başta, kalanı sürücü sırasıyla."""
    adlar = win32print.DeviceCapabilities(yazici, "", win32con.DC_PAPERNAMES)
    idler = win32print.DeviceCapabilities(yazici, "", win32con.DC_PAPERS)
    tumu = {a.strip("\0 "): i for a, i in zip(adlar, idler) if a.strip("\0 ")}
    once = {a: tumu[a] for a in ONCELIKLI_KAGITLAR if a in tumu}
    return {**once, **tumu}


def yazici_ayarlari(yazici):
    """Yazıcının mevcut DEVMODE'u (kağıt, kaset, çift taraf vb. sürücü ayarları)."""
    h = win32print.OpenPrinter(yazici)
    try:
        dm = win32print.GetPrinter(h, 2)["pDevMode"]
    finally:
        win32print.ClosePrinter(h)
    if dm is None:
        raise RuntimeError(f"{yazici} yazıcısının ayarları okunamadı.")
    return dm


def yazici_ayar_penceresi(hwnd, yazici, dm):
    """Sürücünün kendi ayar penceresini açar; Tamam denirse güncel DEVMODE, iptalde None."""
    h = win32print.OpenPrinter(yazici)
    try:
        sonuc = win32print.DocumentProperties(
            hwnd, h, yazici, dm, dm, win32con.DM_IN_PROMPT | win32con.DM_IN_BUFFER | win32con.DM_OUT_BUFFER)
    finally:
        win32print.ClosePrinter(h)
    return dm if sonuc == win32con.IDOK else None


def yazdir(dosyalar, yazici, kagit_kodu, yon, kopya, sifre_sor, dm=None, cikti=None, ilerleme=None):
    """PDF'leri birleştirmeden, sırayla tek baskı işi olarak yazdırır.

    yon: "oto" (her sayfa kendi şekline göre) | "dikey" | "yatay".
    Sayfalar orantılı olarak kağıda sığdırılıp ortalanır; pdfium vektör olarak çizer.
    cikti: "Microsoft Print to PDF" gibi dosyaya basan yazıcılar için çıktı yolu (testte kullanılır).
    ilerleme(dosya_sirasi, yuzde): her sayfadan sonra çağrılır; yüzde tüm kopyalar dahildir.
    Başarılıysa True, şifre sorusu iptal edildiyse False döner.
    """
    # Önce hepsini aç: şifre iptali ya da bozuk dosya yarım baskı işi bırakmasın
    belgeler = []
    try:
        for dosya in dosyalar:
            try:
                sifre = None
                reader = PdfReader(dosya)
                if reader.is_encrypted and not reader.decrypt(""):
                    sifre = sifre_sor(os.path.basename(dosya))
                    if sifre is None:
                        return False
                    if not reader.decrypt(sifre):
                        raise ValueError("Şifre yanlış.")
                belgeler.append(pdfium.PdfDocument(dosya, password=sifre))
            except Exception as e:
                raise RuntimeError(f"{os.path.basename(dosya)}:\n{e}") from e

        dm = dm or yazici_ayarlari(yazici)
        dm.PaperSize = kagit_kodu
        dm.Copies = 1  # kopyaları kendimiz döngüyle basarız: harmanlanmış (1-2-3, 1-2-3)
        dm.Fields |= win32con.DM_PAPERSIZE | win32con.DM_ORIENTATION | win32con.DM_COPIES

        hdc = win32gui.CreateDC("WINSPOOL", yazici, dm)
        try:
            win32print.StartDoc(hdc, ("PDF Birleştirici", cikti, None, 0))
            basilan = [0] * len(belgeler)
            for _ in range(kopya):
                for sira, belge in enumerate(belgeler):
                    for sayfa in belge:
                        w, h = sayfa.get_size()  # sayfa döndürmesi dahil, point
                        yatay = w > h if yon == "oto" else yon == "yatay"
                        dm.Orientation = win32con.DMORIENT_LANDSCAPE if yatay else win32con.DMORIENT_PORTRAIT
                        win32gui.ResetDC(hdc, dm)
                        win32print.StartPage(hdc)
                        pw = win32print.GetDeviceCaps(hdc, win32con.HORZRES)
                        ph = win32print.GetDeviceCaps(hdc, win32con.VERTRES)
                        olcek = min(pw / w, ph / h)
                        dw, dh = int(w * olcek), int(h * olcek)
                        pdfium.raw.FPDF_RenderPage(hdc, sayfa.raw, (pw - dw) // 2, (ph - dh) // 2, dw, dh, 0,
                                                   pdfium.raw.FPDF_ANNOT | pdfium.raw.FPDF_PRINTING)
                        sayfa.close()
                        win32print.EndPage(hdc)
                        basilan[sira] += 1
                        if ilerleme:
                            ilerleme(sira, basilan[sira] * 100 // (len(belge) * kopya))
            win32print.EndDoc(hdc)
        except Exception:
            win32print.AbortDoc(hdc)
            raise
        finally:
            win32gui.DeleteDC(hdc)
        return True
    finally:
        for belge in belgeler:
            belge.close()


# ---------------- Arayüz ----------------

secilen_dosyalar = []

# Material Symbols ikonları (dark-mode.svg / light-mode.svg), 20px PNG olarak gömülü
IKON_AY = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAIASURBVDhP1ZMxiBNREIb/fzckVxzJFRe43UxYixQHXpFCEEHhCgsrvUY5sbC9IgcKNlae2NopWHpiccUJh5WFCBYpRC0sUgS8Juw+ImphkiuEZBkLd8PmZaOtfs3Om/nfz7x984B/HdoJGxFpqGoTgBhjHgOY2Josjp1IEZGWiHwD8JnkIcnC38yQ12EQBGtxHB8A2FTVLyTXVLVtjLlga/OY6zBjdh/AbpJ+Y8kWMmMoIq3E7K4xZi9TOs7Ef8Tu8J6qHhtjHgIAyW7yPW3pFjI1FJEGgFWSz9KfH0VRB8AJgO1qtbo8s3MBU8NkNKCq3ayA5C6AU8Vi8Xmeab1eP+/7/k66zh55KRNPCcNwH8ALklulUumDiLR8378oItsi8kRVX5FcSfVTQ5KfkvBsmkuJouhqcuMC4JHjOK8BHADYAbCsqp1UOzOHIjJS1a4x5lzeEHuet0qySXKDZEFVb5LciOO42u/3v9t61Gq1PRFREblj12xE5FKifZrNu9nFaDRql8vly6p6rVKpDIbD4ftsPaVWq22SPALw1XXdK4PB4Gdam3t6nuetu657BGAdwFtVfek4zsc4jk9INgDcILkFICJ5PQzDdnb/nCF+v+elyWTygOQtAAW7DmDfdd3bvV7vh13INUwJgmBlPB6fcRynqaoFVe2o6rvcC/hv+AX5irReBXuLZAAAAABJRU5ErkJggg=="
IKON_GUNES = "iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAIFSURBVDhPpZSxixNBFMbf25liCWmFFE6S4oQrUlhc4ITYeb1CLAT/hCvOv8HCwiKFhaXlFSdoaXdCGiFXXGe6Yd6bFNsJSXGw7j6L7IbJ3EZW/MHC7rfzfcy8t28BWmCt7THzw1hvIomFJpRSlwAwj/UmWgX+C3uBIqKdcxciokP9EER0nmVZN9T2AonoPEmS2Wq1ugxDkyR5AwCvwrXe+xkifsjz/G2o7yEi2nt/RUS5c25S69baNNyJ9/4xEeXMPI93eI/q2BPYBh0T0XVlFmZeMPMpAIBz7llTGMZCjbX2WCm1QMQuANwAwB0ATETkNyKeGWO+xx6IaxiilPqIiF0ReWGMGRtjngLAk+r1p2j5DrTW9qrvDKBqQJ7nS6XUGhFvjTHj0MDMXwDguYg8KopiE3sTrbVGxGF9iUja6XQ0ImoA+BWGwbbGm+o2bfIerCEzLwDgpCzL8WAwuIFtXYda658isun3+w9iD/ytKcx8KiJz2B7la1mWd4g4BYC0KIqXw+Hwc+yBQ00hoiNjzA9EPENELyJTRHwtIps6jIhGrSbKez8jorVz7qTWiOiIiEbB84iI1t77qzj03uiJyAUi3qZpuqz1oig2iLhrkDFmmSTJNxGZeu/f7QJisizreu9n8QQQ0TUz21ATEc3M7621vVBvRVPgIRqb8j+0Cmz6fR3iDzpFIhsrF0n1AAAAAElFTkSuQmCC"

TEMA_DOSYASI = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "PDF Birlestirici", "tema.txt")


def _baslangic_temasi():
    """Kayıtlı tema, yoksa Windows'un uygulama teması, o da yoksa açık tema."""
    try:
        with open(TEMA_DOSYASI, encoding="utf-8") as f:
            tema = f.read().strip()
        if tema in ("light", "dark"):
            return tema
    except OSError:
        pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as anahtar:
            return "light" if winreg.QueryValueEx(anahtar, "AppsUseLightTheme")[0] else "dark"
    except (OSError, ImportError):
        return "light"


def _baslik_cubugu(tema, pencere=None):
    """Windows 10/11 başlık çubuğunu temaya uydurur; desteklenmiyorsa sessizce geçer."""
    pencere = pencere or root
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(pencere.winfo_id())
        deger = ctypes.c_int(tema == "dark")
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(deger), ctypes.sizeof(deger))
        # Başlık çubuğunun hemen yeniden çizilmesi için
        pencere.wm_attributes("-alpha", 0.99)
        pencere.wm_attributes("-alpha", 1)
    except Exception:
        pass


def _tema_uygula(tema):
    sv_ttk.set_theme(tema)
    # Açık temada "koyuya geç" (ay), koyu temada "açığa geç" (güneş) gösterilir
    tema_butonu.config(image=ikon_ay if tema == "light" else ikon_gunes)
    bos_ipucu.config(background=ttk.Style().lookup("Treeview", "background"))
    _baslik_cubugu(tema)


def tema_degistir():
    tema = "dark" if sv_ttk.get_theme() == "light" else "light"
    _tema_uygula(tema)
    try:
        os.makedirs(os.path.dirname(TEMA_DOSYASI), exist_ok=True)
        with open(TEMA_DOSYASI, "w", encoding="utf-8") as f:
            f.write(tema)
    except OSError:
        pass  # Tercih kaydedilemezse uygulama yine çalışır


def _mb(dosya):
    try:
        return os.path.getsize(dosya) / (1024 * 1024)
    except OSError:
        return 0


def _yenile():
    """Durum satırını, boş liste ipucunu ve Birleştir butonunu günceller."""
    n = len(secilen_dosyalar)
    if n:
        bos_ipucu.place_forget()
        toplam = sum(_mb(d) for d in secilen_dosyalar)
        durum.config(text=f"{n} dosya  ·  {toplam:.1f} MB")
        btn_birlestir.state(["!disabled"])
        btn_yazdir.state(["!disabled"])
        btn_ayir.state(["!disabled"] if tablo.selection() else ["disabled"])
    else:
        btn_ayir.state(["disabled"])
        bos_ipucu.place(relx=0.5, rely=0.5, anchor="center")
        durum.config(text="Henüz dosya eklenmedi")
        btn_birlestir.state(["disabled"])
        btn_yazdir.state(["disabled"])


def dosya_ekle():
    dosyalar = filedialog.askopenfilenames(
        title="Birleştirilecek PDF Dosyalarını Seçin",
        filetypes=[("PDF Dosyaları", "*.pdf")]
    )
    for dosya in dosyalar:
        if dosya not in secilen_dosyalar:
            secilen_dosyalar.append(dosya)
            klasor = os.path.basename(os.path.dirname(dosya))
            tablo.insert("", tk.END, values=(os.path.basename(dosya), klasor, f"{_mb(dosya):.1f} MB", ""))
    _yenile()


def secileni_sil():
    secili = tablo.selection()
    if not secili:
        messagebox.showwarning("Uyarı", "Lütfen kaldırmak için listeden bir dosya seçin!")
        return
    iid = secili[0]
    secilen_dosyalar.pop(tablo.index(iid))
    tablo.delete(iid)
    _yenile()


def tumunu_temizle():
    secilen_dosyalar.clear()
    tablo.delete(*tablo.get_children())
    _yenile()


def _tasi(yon):
    secili = tablo.selection()
    if not secili:
        return
    iid = secili[0]
    index = tablo.index(iid)
    hedef = index + yon
    if not 0 <= hedef < len(secilen_dosyalar):
        return
    tablo.move(iid, "", hedef)
    tablo.see(iid)
    secilen_dosyalar[index], secilen_dosyalar[hedef] = secilen_dosyalar[hedef], secilen_dosyalar[index]


def yukari_tasi():
    _tasi(-1)


def asagi_tasi():
    _tasi(1)


def _sifre_sor(dosya_adi):
    return simpledialog.askstring("Şifreli PDF", f"{dosya_adi} şifreli.\nŞifreyi girin:", show="*", parent=root)


def pdf_birlestir():
    if not secilen_dosyalar:
        messagebox.showwarning("Uyarı", "Birleştirilecek hiç PDF seçilmedi!")
        return

    kayit_yeri = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Dosyaları", "*.pdf")],
        title="Birleştirilen Dosyayı Kaydet"
    )
    if not kayit_yeri:
        return

    root.config(cursor="watch")
    root.update_idletasks()
    try:
        if birlestir(secilen_dosyalar, kayit_yeri, _sifre_sor):
            messagebox.showinfo("Başarılı!", f"PDF'ler başarıyla birleştirildi:\n{kayit_yeri}")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu:\n{e}")
    finally:
        root.config(cursor="")


YESIL = "#16a34a"


def _ilerleme_goster(sira, yuzde):
    """Yazdırılan satırın 'Yazdırma' hücresinde yeşil çubuk; bitince satır yeşil zemin/beyaz yazı."""
    iid = tablo.get_children()[sira]
    tablo.set(iid, "yazdirma", f"{yuzde}%")
    if yuzde >= 100:
        ilerleme_cubugu.place_forget()
        tablo.item(iid, tags=("bitti",))
    else:
        tablo.see(iid)
        root.update_idletasks()  # see() sonrası bbox güncel olsun
        kutu = tablo.bbox(iid, "yazdirma")
        if kutu:
            x, y, w, h = kutu
            ilerleme_cubugu.place(in_=tablo, x=x, y=y, width=w, height=h)
            ilerleme_cubugu.config(background=ttk.Style().lookup("Treeview", "background"))
            ilerleme_cubugu.delete("all")
            ilerleme_cubugu.create_rectangle(0, 0, w * yuzde / 100, h, fill=YESIL, width=0)
            renk = "white" if yuzde >= 50 else ttk.Style().lookup("Treeview", "foreground")
            ilerleme_cubugu.create_text(w / 2, h / 2, text=f"{yuzde}%", fill=renk)
    # ponytail: baskı ana thread'de; çok uzun işlerde pencere "yanıt vermiyor" görünebilir -> o zaman thread'e taşı
    root.update_idletasks()


def _yazdirmayi_baslat(yazici, kagit_kodu, yon, kopya, dm):
    for iid in tablo.get_children():
        tablo.set(iid, "yazdirma", "")
        tablo.item(iid, tags=())
    tablo.selection_remove(tablo.selection())  # seçili satırın rengi yeşili örtmesin
    root.config(cursor="watch")
    try:
        if yazdir(secilen_dosyalar, yazici, kagit_kodu, yon, kopya, _sifre_sor, dm=dm, ilerleme=_ilerleme_goster):
            messagebox.showinfo("Yazdırıldı", f"{len(secilen_dosyalar)} dosya yazıcıya gönderildi:\n{yazici}")
    except Exception as e:
        messagebox.showerror("Hata", f"Yazdırılamadı:\n{e}")
    finally:
        ilerleme_cubugu.place_forget()
        root.config(cursor="")


def yazdir_penceresi():
    if not secilen_dosyalar:
        return
    try:
        adlar, varsayilan = yazicilar()
    except Exception as e:
        messagebox.showerror("Hata", f"Yazıcılar listelenemedi:\n{e}")
        return
    if not adlar:
        messagebox.showwarning("Uyarı", "Bu bilgisayarda yüklü yazıcı bulunamadı.")
        return

    pen = tk.Toplevel(root)
    pen.title("Yazdır")
    pen.resizable(False, False)
    pen.transient(root)
    govde = ttk.Frame(pen, padding=20)
    govde.pack(fill=tk.BOTH, expand=True)
    govde.columnconfigure(1, weight=1)

    ttk.Label(govde, text=f"{len(secilen_dosyalar)} dosya listedeki sırayla, birleştirilmeden yazdırılacak.",
              foreground="gray").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

    durum_ = {"dm": None, "kagitlar": {}}  # sürücü ayarları penceresinden gelen DEVMODE
    yazici = tk.StringVar(value=varsayilan if varsayilan in adlar else adlar[0])
    kagit = tk.StringVar()
    yon = tk.StringVar(value="oto")
    kopya = tk.IntVar(value=1)

    ttk.Label(govde, text="Yazıcı").grid(row=1, column=0, sticky="w", pady=4)
    cb_yazici = ttk.Combobox(govde, textvariable=yazici, values=adlar, state="readonly", width=34)
    cb_yazici.grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(govde, text="Kağıt").grid(row=2, column=0, sticky="w", pady=4)
    cb_kagit = ttk.Combobox(govde, textvariable=kagit, state="readonly", height=15)
    cb_kagit.grid(row=2, column=1, sticky="ew", pady=4)

    def kagidi_sec(kod):
        ad = next((a for a, k in durum_["kagitlar"].items() if k == kod), None)
        kagit.set(ad or ("A4" if "A4" in durum_["kagitlar"] else next(iter(durum_["kagitlar"]), "")))

    def yazici_degisti(_=None):
        try:
            durum_["kagitlar"] = kagitlar(yazici.get())
            durum_["dm"] = yazici_ayarlari(yazici.get())
        except Exception as e:
            durum_["kagitlar"], durum_["dm"] = {}, None
            messagebox.showerror("Hata", f"Yazıcı bilgileri okunamadı:\n{e}", parent=pen)
        cb_kagit.config(values=list(durum_["kagitlar"]))
        kagidi_sec(durum_["dm"].PaperSize if durum_["dm"] else None)

    def ayarlar():
        if durum_["dm"] is None:
            return
        try:
            dm = yazici_ayar_penceresi(int(pen.wm_frame(), 16), yazici.get(), durum_["dm"])
        except Exception as e:
            messagebox.showerror("Hata", f"Yazıcı ayarları açılamadı:\n{e}", parent=pen)
            return
        if dm is not None:
            durum_["dm"] = dm
            kagidi_sec(dm.PaperSize)

    cb_yazici.bind("<<ComboboxSelected>>", yazici_degisti)
    ttk.Button(govde, text="Ayarlar…", command=ayarlar).grid(row=1, column=2, padx=(8, 0), pady=4)

    ttk.Label(govde, text="Yön").grid(row=3, column=0, sticky="w", pady=4)
    yonler = ttk.Frame(govde)
    yonler.grid(row=3, column=1, columnspan=2, sticky="w", pady=4)
    for deger, metin in (("oto", "Otomatik"), ("dikey", "Dikey"), ("yatay", "Yatay")):
        ttk.Radiobutton(yonler, text=metin, value=deger, variable=yon).pack(side=tk.LEFT, padx=(0, 12))
    ttk.Label(govde, text="Otomatik: yatay sayfalar yatay, dikey sayfalar dikey basılır.",
              foreground="gray").grid(row=4, column=1, columnspan=2, sticky="w")

    ttk.Label(govde, text="Kopya").grid(row=5, column=0, sticky="w", pady=(10, 4))
    ttk.Spinbox(govde, from_=1, to=99, textvariable=kopya, width=6).grid(row=5, column=1, sticky="w", pady=(10, 4))

    def yazdir_tikla():
        try:
            adet = int(kopya.get())
            if not 1 <= adet <= 99:
                raise ValueError
        except (ValueError, tk.TclError):
            messagebox.showwarning("Uyarı", "Kopya sayısı 1 ile 99 arasında olmalı.", parent=pen)
            return
        if kagit.get() not in durum_["kagitlar"] or durum_["dm"] is None:
            messagebox.showwarning("Uyarı", "Lütfen bir yazıcı ve kağıt seçin.", parent=pen)
            return
        ayarlar_ = (yazici.get(), durum_["kagitlar"][kagit.get()], yon.get(), adet)
        pen.destroy()
        _yazdirmayi_baslat(*ayarlar_, durum_["dm"])

    butonlar = ttk.Frame(govde)
    butonlar.grid(row=6, column=0, columnspan=3, sticky="e", pady=(16, 0))
    ttk.Button(butonlar, text="İptal", command=pen.destroy).pack(side=tk.RIGHT, padx=(8, 0))
    ttk.Button(butonlar, text="Yazdır", style="Accent.TButton", command=yazdir_tikla).pack(side=tk.RIGHT)

    yazici_degisti()
    pen.bind("<Escape>", lambda e: pen.destroy())
    pen.grab_set()
    pen.after(50, lambda: _baslik_cubugu(sv_ttk.get_theme(), pen))


def ayir_penceresi():
    secili = tablo.selection()
    if not secili:
        return
    dosya = secilen_dosyalar[tablo.index(secili[0])]
    try:
        r = PdfReader(dosya)
        bilgi = f"{len(r.pages)} sayfa" if not r.is_encrypted or r.decrypt("") else "şifreli"
    except Exception:
        bilgi = "okunamadı"

    pen = tk.Toplevel(root)
    pen.title("Ayır")
    pen.resizable(False, False)
    pen.transient(root)
    govde = ttk.Frame(pen, padding=20)
    govde.pack(fill=tk.BOTH, expand=True)
    govde.columnconfigure(1, weight=1)

    ttk.Label(govde, text=f"{os.path.basename(dosya)}  ·  {bilgi}",
              font=("Segoe UI Semibold", 11)).grid(row=0, column=0, columnspan=3, sticky="w")
    ttk.Label(govde, text="Parçalar seçeceğiniz klasöre ayrı PDF dosyaları olarak kaydedilir.",
              foreground="gray").grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

    mod = tk.StringVar(value="aralik")
    aralik, sec = tk.StringVar(value="1-5, 6-10"), tk.StringVar(value="1, 3")
    n, mb = tk.StringVar(value="2"), tk.StringVar(value="10")
    girdiler = {
        "aralik": (ttk.Entry(govde, textvariable=aralik, width=24), "Her aralık ayrı dosya"),
        "tek": (None, "Her sayfa ayrı dosya"),
        "n": (ttk.Spinbox(govde, from_=1, to=9999, textvariable=n, width=8), "sayfa"),
        "sec": (ttk.Entry(govde, textvariable=sec, width=24), "Hepsi tek dosyada"),
        "boyut": (ttk.Spinbox(govde, from_=1, to=500, textvariable=mb, width=8), "MB (en fazla)"),
        "yerimi": (None, "Her bölüm ayrı dosya"),
    }
    basliklar = {"aralik": "Sayfa aralıkları", "tek": "Her sayfayı ayır", "n": "Her N sayfada bir",
                 "sec": "Belirli sayfaları çıkar", "boyut": "Boyuta göre", "yerimi": "Yer imlerine göre"}

    def mod_degisti():
        for m, (girdi, _) in girdiler.items():
            if girdi:
                girdi.state(["!disabled"] if m == mod.get() else ["disabled"])

    for satir, (m, (girdi, ipucu)) in enumerate(girdiler.items(), start=2):
        ttk.Radiobutton(govde, text=basliklar[m], value=m, variable=mod, command=mod_degisti).grid(
            row=satir, column=0, sticky="w", pady=4, padx=(0, 16))
        if girdi:
            girdi.grid(row=satir, column=1, sticky="w", pady=4)
        ttk.Label(govde, text=ipucu, foreground="gray").grid(
            row=satir, column=2 if girdi else 1, columnspan=1 if girdi else 2, sticky="w", padx=(8, 0))

    def ayir_tikla():
        m = mod.get()
        try:
            deger = {"aralik": aralik.get, "sec": sec.get,
                     "n": lambda: int(n.get()),
                     "boyut": lambda: float(mb.get().replace(",", "."))}.get(m, lambda: None)()
            if m in ("n", "boyut") and not deger > 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Uyarı", "Lütfen 0'dan büyük bir sayı girin.", parent=pen)
            return
        klasor = filedialog.askdirectory(title="Parçaların Kaydedileceği Klasör",
                                         initialdir=os.path.dirname(dosya), parent=pen)
        if not klasor:
            return

        def uzerine_yaz_sor(mevcut):
            ornek = "\n".join(os.path.basename(y) for y in mevcut[:5]) + ("\n…" if len(mevcut) > 5 else "")
            return messagebox.askyesno("Dosyalar Var", f"{len(mevcut)} dosya zaten var:\n{ornek}\n\n"
                                                       "Üzerine yazılsın mı?", parent=pen)

        pen.config(cursor="watch")
        pen.update_idletasks()
        try:
            yollar = ayir(dosya, m, deger, klasor, _sifre_sor, uzerine_yaz_sor)
        except Exception as e:
            messagebox.showerror("Hata", f"Ayrılamadı:\n{e}", parent=pen)  # pencere açık kalır, düzeltip tekrar denenir
            return
        finally:
            pen.config(cursor="")
        if yollar is None:
            return
        mesaj = f"{len(yollar)} dosya oluşturuldu:\n{klasor}"
        if m == "boyut":
            buyuk = sum(_mb(y) > deger for y in yollar)
            if buyuk:
                mesaj += f"\n\nUyarı: {buyuk} parça tek sayfası {deger:g} MB'tan büyük olduğu için sınırı aşıyor."
        pen.destroy()
        messagebox.showinfo("Başarılı!", mesaj)

    butonlar = ttk.Frame(govde)
    butonlar.grid(row=len(girdiler) + 2, column=0, columnspan=3, sticky="e", pady=(16, 0))
    ttk.Button(butonlar, text="İptal", command=pen.destroy).pack(side=tk.RIGHT, padx=(8, 0))
    ttk.Button(butonlar, text="Ayır", style="Accent.TButton", command=ayir_tikla).pack(side=tk.RIGHT)

    mod_degisti()
    pen.bind("<Escape>", lambda e: pen.destroy())
    pen.grab_set()
    pen.after(50, lambda: _baslik_cubugu(sv_ttk.get_theme(), pen))


if __name__ == "__main__":
    root = tk.Tk()
    root.title("PDF Birleştirici")
    root.geometry("780x500")
    root.minsize(620, 400)
    ikon_ay = tk.PhotoImage(data=IKON_AY)
    ikon_gunes = tk.PhotoImage(data=IKON_GUNES)

    ana = ttk.Frame(root, padding=20)
    ana.pack(fill=tk.BOTH, expand=True)
    ana.columnconfigure(0, weight=1)
    ana.rowconfigure(1, weight=1)

    # Başlık
    ust = ttk.Frame(ana)
    ust.grid(row=0, column=0, sticky="w", pady=(0, 15))
    tema_butonu = ttk.Button(ana, style="Toolbutton", command=tema_degistir)
    tema_butonu.grid(row=0, column=1, sticky="ne")
    ttk.Label(ust, text="PDF Birleştirici", font=("Segoe UI Semibold", 18)).pack(anchor="w")
    ttk.Label(ust, text="Dosyaları ekleyin, sıralayın; tek PDF olarak kaydedin, sırayla yazdırın ya da parçalara ayırın.",
              foreground="gray").pack(anchor="w")

    # Dosya tablosu
    frame_liste = ttk.Frame(ana)
    frame_liste.grid(row=1, column=0, sticky="nsew")
    frame_liste.rowconfigure(0, weight=1)
    frame_liste.columnconfigure(0, weight=1)

    tablo = ttk.Treeview(frame_liste, columns=("dosya", "klasor", "boyut", "yazdirma"), show="headings",
                         selectmode="browse")
    for kolon, baslik, genislik, hiza in (("dosya", "Dosya", 280, "w"),
                                          ("klasor", "Klasör", 150, "w"),
                                          ("boyut", "Boyut", 80, "e"),
                                          ("yazdirma", "Yazdırma", 90, "center")):
        tablo.heading(kolon, text=baslik, anchor=hiza)
        tablo.column(kolon, width=genislik, anchor=hiza, stretch=kolon not in ("boyut", "yazdirma"))
    tablo.tag_configure("bitti", background=YESIL, foreground="white")
    ilerleme_cubugu = tk.Canvas(frame_liste, highlightthickness=0, borderwidth=0)
    tablo.grid(row=0, column=0, sticky="nsew")
    kaydir = ttk.Scrollbar(frame_liste, orient=tk.VERTICAL, command=tablo.yview)
    kaydir.grid(row=0, column=1, sticky="ns")
    tablo.config(yscrollcommand=kaydir.set)
    tablo.bind("<Delete>", lambda e: secileni_sil())
    tablo.bind("<<TreeviewSelect>>", lambda e: _yenile())

    bos_ipucu = ttk.Label(frame_liste, text="Henüz PDF eklenmedi\n\"PDF Ekle\" ile başlayın",
                          justify="center", foreground="gray")

    # Sağ panel butonları
    yan = ttk.Frame(ana)
    yan.grid(row=1, column=1, sticky="ns", padx=(12, 0))

    def yan_buton(metin, komut, stil="TButton"):
        ttk.Button(yan, text=metin, command=komut, style=stil, width=16).pack(fill=tk.X, pady=3)

    yan_buton("＋  PDF Ekle", dosya_ekle, "Accent.TButton")
    yan_buton("✕  Kaldır", secileni_sil)
    ttk.Separator(yan).pack(fill=tk.X, pady=10)
    yan_buton("▲  Yukarı", yukari_tasi)
    yan_buton("▼  Aşağı", asagi_tasi)
    ttk.Separator(yan).pack(fill=tk.X, pady=10)
    yan_buton("Tümünü Temizle", tumunu_temizle)

    # Alt çubuk
    alt = ttk.Frame(ana)
    alt.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(15, 0))
    durum = ttk.Label(alt, foreground="gray")
    durum.pack(side=tk.LEFT)
    btn_birlestir = ttk.Button(alt, text="Birleştir ve Kaydet", style="Accent.TButton", command=pdf_birlestir)
    btn_birlestir.pack(side=tk.RIGHT, ipadx=12, ipady=2)
    btn_yazdir = ttk.Button(alt, text="🖨  Yazdır…", command=yazdir_penceresi)
    btn_yazdir.pack(side=tk.RIGHT, padx=(0, 8), ipadx=8, ipady=2)
    btn_ayir = ttk.Button(alt, text="✂  Ayır…", command=ayir_penceresi)
    btn_ayir.pack(side=tk.RIGHT, padx=(0, 8), ipadx=8, ipady=2)

    tema = _baslangic_temasi()
    _tema_uygula(tema)
    _yenile()
    root.after(50, lambda: _baslik_cubugu(tema))  # pencere ekrana geldikten sonra başlık çubuğu
    root.mainloop()
