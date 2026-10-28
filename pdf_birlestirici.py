import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pypdf import PdfWriter

# Seçilen dosya yollarını tutacak liste
secilen_dosyalar = []
MAX_BOYUT_MB = 500  # Maksimum toplam dosya boyutu sınırı (RAM koruması)

def dosya_ekle():
    global secilen_dosyalar
    dosyalar = filedialog.askopenfilenames(
        title="Birleştirilecek PDF Dosyalarını Seçin",
        filetypes=[("PDF Dosyaları", "*.pdf")]
    )
    for dosya in dosyalar:
        if dosya not in secilen_dosyalar:
            secilen_dosyalar.append(dosya)
            dosya_listesi.insert(tk.END, os.path.basename(dosya))

def secileni_sil():
    global secilen_dosyalar
    secili_indexler = dosya_listesi.curselection()
    if not secili_indexler:
        messagebox.showwarning("Uyarı", "Lütfen silmek için listeden bir dosya seçin!")
        return
    
    for index in reversed(secili_indexler):
        dosya_listesi.delete(index)
        secilen_dosyalar.pop(index)

def yukari_tasi():
    global secilen_dosyalar
    secili_indexler = dosya_listesi.curselection()
    if not secili_indexler:
        return
    
    index = secili_indexler[0]
    if index == 0:
        return
        
    dosya_adi = dosya_listesi.get(index)
    dosya_listesi.delete(index)
    dosya_listesi.insert(index - 1, dosya_adi)
    dosya_listesi.selection_set(index - 1)
    
    secilen_dosyalar[index], secilen_dosyalar[index - 1] = secilen_dosyalar[index - 1], secilen_dosyalar[index]

def asagi_tasi():
    global secilen_dosyalar
    secili_indexler = dosya_listesi.curselection()
    if not secili_indexler:
        return
    
    index = secili_indexler[0]
    if index == dosya_listesi.size() - 1:
        return
        
    dosya_adi = dosya_listesi.get(index)
    dosya_listesi.delete(index)
    dosya_listesi.insert(index + 1, dosya_adi)
    dosya_listesi.selection_set(index + 1)
    
    secilen_dosyalar[index], secilen_dosyalar[index + 1] = secilen_dosyalar[index + 1], secilen_dosyalar[index]

def pdf_birlestir():
    global secilen_dosyalar
    if not secilen_dosyalar:
        messagebox.showwarning("Uyarı", "Birleştirilecek hiç PDF seçilmedi!")
        return

    # Boyut Kontrolü (RAM koruması)
    toplam_boyut = sum(os.path.getsize(f) for f in secilen_dosyalar) / (1024 * 1024)
    if toplam_boyut > MAX_BOYUT_MB:
        messagebox.showerror(
            "Boyut Sınırı Aşıldı!", 
            f"Seçilen dosyaların toplam boyutu ({toplam_boyut:.1f} MB),\n"
            f"izin verilen maksimum {MAX_BOYUT_MB} MB sınırını aşıyor.\n"
            f"Lütfen daha az veya daha küçük dosyalar seçin."
        )
        return

    kayit_yeri = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF Dosyaları", "*.pdf")],
        title="Birleştirilen Dosyayı Kaydet"
    )
    
    if not kayit_yeri:
        return

    try:
        merger = PdfWriter()
        for dosya in secilen_dosyalar:
            merger.append(dosya)

        with open(kayit_yeri, "wb") as cikis_dosyasi:
            merger.write(cikis_dosyasi)
            
        merger.close()
        messagebox.showinfo("Başarılı!", f"PDF'ler başarıyla birleştirildi:\n{kayit_yeri}")
    
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu:\n{str(e)}")

# Ana Pencere
root = tk.Tk()
root.title("PDF Birleştirici & Sıralayıcı")
root.geometry("450x450")
root.resizable(False, False)

# Başlık
baslik_etiketi = tk.Label(root, text="PDF Düzenleme ve Birleştirme", font=("Arial", 12, "bold"))
baslik_etiketi.pack(pady=10)

# Liste Kutusu
frame_liste = tk.Frame(root)
frame_liste.pack(pady=5)

dosya_listesi = tk.Listbox(frame_liste, width=50, height=12, selectmode=tk.SINGLE, font=("Arial", 10))
dosya_listesi.pack(side=tk.LEFT, fill=tk.BOTH)

# Butonlar Paneli
frame_butonlar = tk.Frame(root)
frame_butonlar.pack(pady=10)

btn_ekle = tk.Button(frame_butonlar, text="Dosya Ekle", command=dosya_ekle, bg="#4CAF50", fg="white", width=12, font=("Arial", 9, "bold"))
btn_ekle.grid(row=0, column=0, padx=5)

btn_sil = tk.Button(frame_butonlar, text="Seçileni Sil", command=secileni_sil, bg="#f44336", fg="white", width=12, font=("Arial", 9, "bold"))
btn_sil.grid(row=0, column=1, padx=5)

btn_yukari = tk.Button(frame_butonlar, text="⬆ Yukarı", command=yukari_tasi, width=10, font=("Arial", 9))
btn_yukari.grid(row=1, column=0, padx=5, pady=5)

btn_asagi = tk.Button(frame_butonlar, text="⬇ Aşağı", command=asagi_tasi, width=10, font=("Arial", 9))
btn_asagi.grid(row=1, column=1, padx=5, pady=5)

# Birleştirme Butonu
btn_birlestir = tk.Button(
    root, 
    text="PDF'leri Birleştir ve Kaydet", 
    command=pdf_birlestir, 
    bg="#2196F3", 
    fg="white", 
    font=("Arial", 10, "bold"), 
    width=38, 
    pady=8
)
btn_birlestir.pack(pady=10)

root.mainloop()