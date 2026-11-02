import os
import tempfile
from pypdf import PdfReader, PdfWriter
from pdf_birlestirici import birlestir, kagitlar, yazdir, yazicilar


def pdf_yap(yol, sayfa, sifre=None, boyut=(100, 100)):
    w = PdfWriter()
    for _ in range(sayfa):
        w.add_blank_page(*boyut)
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

    # Yazdırma: Windows'un "Microsoft Print to PDF" yazıcısına dosya olarak basılır
    PDF_YAZICI = "Microsoft Print to PDF"
    if PDF_YAZICI in yazicilar()[0]:
        dikey, yatay = os.path.join(d, "dikey.pdf"), os.path.join(d, "yatay.pdf")
        pdf_yap(dikey, 1, boyut=(595, 842))
        pdf_yap(yatay, 2, boyut=(842, 595), sifre="gizli")

        def basilan(kagit, yon, kopya=1):
            yol = os.path.join(d, f"baski_{kagit}_{yon}_{kopya}.pdf")
            assert yazdir([dikey, yatay], PDF_YAZICI, kagitlar(PDF_YAZICI)[kagit], yon, kopya,
                          lambda ad: "gizli", cikti=yol) is True
            return [(round(float(p.mediabox.width)), round(float(p.mediabox.height))) for p in PdfReader(yol).pages]

        A4D, A4Y = (595, 842), (842, 595)
        assert basilan("A4", "oto") == [A4D, A4Y, A4Y]  # sıra + sayfa bazlı yön
        assert basilan("A4", "dikey") == [A4D] * 3
        assert basilan("A5", "yatay") == [(595, 420)] * 3  # kağıt boyutu uygulanır
        assert len(basilan("A4", "oto", kopya=2)) == 6

        # İlerleme: dosya sırası + yüzde, kopyalar dahil, her dosya 100'de biter
        olaylar = []
        yazdir([dikey, yatay], PDF_YAZICI, 9, "oto", 2, lambda ad: "gizli",
               cikti=os.path.join(d, "ilerleme.pdf"), ilerleme=lambda i, y: olaylar.append((i, y)))
        assert olaylar == [(0, 50), (1, 25), (1, 50), (0, 100), (1, 75), (1, 100)], olaylar
        assert list(kagitlar(PDF_YAZICI))[:2] == ["A4", "A3"]  # yaygın kağıtlar başta

        # Şifre iptali: hiçbir şey basılmaz
        assert yazdir([yatay], PDF_YAZICI, 9, "oto", 1, lambda ad: None, cikti=os.path.join(d, "x.pdf")) is False
        assert not os.path.exists(os.path.join(d, "x.pdf"))
    else:
        print(f"UYARI: '{PDF_YAZICI}' yok, yazdırma testi atlandı")

print("OK")
