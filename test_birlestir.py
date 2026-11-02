import os
import tempfile
from pypdf import PdfReader, PdfWriter
from pdf_birlestirici import birlestir


def pdf_yap(yol, sayfa, sifre=None):
    w = PdfWriter()
    for _ in range(sayfa):
        w.add_blank_page(100, 100)
    if sifre:
        w.encrypt(sifre)
    w.write(yol)


def hata_bekle(tip, fn):
    try:
        fn()
    except tip as e:
        return str(e)
    raise AssertionError(f"{tip.__name__} bekleniyordu")


with tempfile.TemporaryDirectory() as d:
    a, b, c, out = (os.path.join(d, n) for n in ("a.pdf", "b.pdf", "c.pdf", "out.pdf"))
    pdf_yap(a, 1)
    pdf_yap(b, 2)
    pdf_yap(c, 3, sifre="gizli")

    # Normal + şifreli birleştirme, sıra korunur
    assert birlestir([b, a, c], out, lambda ad: "gizli") is True
    assert len(PdfReader(out).pages) == 6

    # Şifre iptal edilirse False
    assert birlestir([c], out, lambda ad: None) is False

    # Yanlış şifre: hata mesajında dosya adı var
    assert "c.pdf" in hata_bekle(RuntimeError, lambda: birlestir([a, c], out, lambda ad: "yanlis"))

    # Girdi dosyasının üzerine yazma engellenir, orijinal bozulmaz
    hata_bekle(ValueError, lambda: birlestir([a, b], a, lambda ad: None))
    assert len(PdfReader(a).pages) == 1

    # Eksik dosya: anlaşılır hata
    assert "yok.pdf" in hata_bekle(ValueError, lambda: birlestir([os.path.join(d, "yok.pdf")], out, lambda ad: None))

print("OK")
