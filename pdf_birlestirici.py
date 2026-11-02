import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import sv_ttk
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


def _baslik_cubugu(tema):
    """Windows 10/11 başlık çubuğunu temaya uydurur; desteklenmiyorsa sessizce geçer."""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        deger = ctypes.c_int(tema == "dark")
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(deger), ctypes.sizeof(deger))
        # Başlık çubuğunun hemen yeniden çizilmesi için
        root.wm_attributes("-alpha", 0.99)
        root.wm_attributes("-alpha", 1)
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
    else:
        bos_ipucu.place(relx=0.5, rely=0.5, anchor="center")
        durum.config(text="Henüz dosya eklenmedi")
        btn_birlestir.state(["disabled"])


def dosya_ekle():
    dosyalar = filedialog.askopenfilenames(
        title="Birleştirilecek PDF Dosyalarını Seçin",
        filetypes=[("PDF Dosyaları", "*.pdf")]
    )
    for dosya in dosyalar:
        if dosya not in secilen_dosyalar:
            secilen_dosyalar.append(dosya)
            klasor = os.path.basename(os.path.dirname(dosya))
            tablo.insert("", tk.END, values=(os.path.basename(dosya), klasor, f"{_mb(dosya):.1f} MB"))
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
    ttk.Label(ust, text="Dosyaları ekleyin, sıralayın ve tek bir PDF olarak kaydedin.",
              foreground="gray").pack(anchor="w")

    # Dosya tablosu
    frame_liste = ttk.Frame(ana)
    frame_liste.grid(row=1, column=0, sticky="nsew")
    frame_liste.rowconfigure(0, weight=1)
    frame_liste.columnconfigure(0, weight=1)

    tablo = ttk.Treeview(frame_liste, columns=("dosya", "klasor", "boyut"), show="headings", selectmode="browse")
    for kolon, baslik, genislik, hiza in (("dosya", "Dosya", 300, "w"),
                                          ("klasor", "Klasör", 170, "w"),
                                          ("boyut", "Boyut", 80, "e")):
        tablo.heading(kolon, text=baslik, anchor=hiza)
        tablo.column(kolon, width=genislik, anchor=hiza, stretch=kolon != "boyut")
    tablo.grid(row=0, column=0, sticky="nsew")
    kaydir = ttk.Scrollbar(frame_liste, orient=tk.VERTICAL, command=tablo.yview)
    kaydir.grid(row=0, column=1, sticky="ns")
    tablo.config(yscrollcommand=kaydir.set)
    tablo.bind("<Delete>", lambda e: secileni_sil())

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

    tema = _baslangic_temasi()
    _tema_uygula(tema)
    _yenile()
    root.after(50, lambda: _baslik_cubugu(tema))  # pencere ekrana geldikten sonra başlık çubuğu
    root.mainloop()
