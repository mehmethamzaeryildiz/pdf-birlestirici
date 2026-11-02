import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
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


def _etiket(dosya):
    # Aynı adlı dosyaları ayırt etmek için klasör adını da göster
    return f"{os.path.basename(dosya)}   ({os.path.basename(os.path.dirname(dosya))})"


def dosya_ekle():
    dosyalar = filedialog.askopenfilenames(
        title="Birleştirilecek PDF Dosyalarını Seçin",
        filetypes=[("PDF Dosyaları", "*.pdf")]
    )
    for dosya in dosyalar:
        if dosya not in secilen_dosyalar:
            secilen_dosyalar.append(dosya)
            dosya_listesi.insert(tk.END, _etiket(dosya))


def secileni_sil():
    secili_indexler = dosya_listesi.curselection()
    if not secili_indexler:
        messagebox.showwarning("Uyarı", "Lütfen silmek için listeden bir dosya seçin!")
        return
    for index in reversed(secili_indexler):
        dosya_listesi.delete(index)
        secilen_dosyalar.pop(index)


def tumunu_temizle():
    secilen_dosyalar.clear()
    dosya_listesi.delete(0, tk.END)


def _tasi(yon):
    secili_indexler = dosya_listesi.curselection()
    if not secili_indexler:
        return
    index = secili_indexler[0]
    hedef = index + yon
    if not 0 <= hedef < dosya_listesi.size():
        return
    etiket = dosya_listesi.get(index)
    dosya_listesi.delete(index)
    dosya_listesi.insert(hedef, etiket)
    dosya_listesi.selection_set(hedef)
    dosya_listesi.see(hedef)
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

    try:
        if birlestir(secilen_dosyalar, kayit_yeri, _sifre_sor):
            messagebox.showinfo("Başarılı!", f"PDF'ler başarıyla birleştirildi:\n{kayit_yeri}")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("PDF Birleştirici & Sıralayıcı")
    root.geometry("520x480")
    root.minsize(420, 400)

    tk.Label(root, text="PDF Düzenleme ve Birleştirme", font=("Arial", 12, "bold")).pack(pady=10)

    # Liste kutusu + kaydırma çubukları
    frame_liste = tk.Frame(root)
    frame_liste.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
    frame_liste.rowconfigure(0, weight=1)
    frame_liste.columnconfigure(0, weight=1)

    dosya_listesi = tk.Listbox(frame_liste, selectmode=tk.SINGLE, font=("Arial", 10))
    dosya_listesi.grid(row=0, column=0, sticky="nsew")
    kaydir_y = tk.Scrollbar(frame_liste, orient=tk.VERTICAL, command=dosya_listesi.yview)
    kaydir_y.grid(row=0, column=1, sticky="ns")
    kaydir_x = tk.Scrollbar(frame_liste, orient=tk.HORIZONTAL, command=dosya_listesi.xview)
    kaydir_x.grid(row=1, column=0, sticky="ew")
    dosya_listesi.config(yscrollcommand=kaydir_y.set, xscrollcommand=kaydir_x.set)

    # Butonlar Paneli
    frame_butonlar = tk.Frame(root)
    frame_butonlar.pack(pady=10)

    tk.Button(frame_butonlar, text="Dosya Ekle", command=dosya_ekle, bg="#4CAF50", fg="white", width=12,
              font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5)
    tk.Button(frame_butonlar, text="Seçileni Sil", command=secileni_sil, bg="#f44336", fg="white", width=12,
              font=("Arial", 9, "bold")).grid(row=0, column=1, padx=5)
    tk.Button(frame_butonlar, text="Tümünü Temizle", command=tumunu_temizle, width=12,
              font=("Arial", 9)).grid(row=0, column=2, padx=5)
    tk.Button(frame_butonlar, text="⬆ Yukarı", command=yukari_tasi, width=12,
              font=("Arial", 9)).grid(row=1, column=0, padx=5, pady=5)
    tk.Button(frame_butonlar, text="⬇ Aşağı", command=asagi_tasi, width=12,
              font=("Arial", 9)).grid(row=1, column=1, padx=5, pady=5)

    tk.Button(root, text="PDF'leri Birleştir ve Kaydet", command=pdf_birlestir, bg="#2196F3", fg="white",
              font=("Arial", 10, "bold"), width=38, pady=8).pack(pady=10)

    root.mainloop()
