import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors


def build():
    filename = f"result_excel/slip_gaji_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    print(width, height)

    c.drawImage("excel_template/logo_pdam.png", 10, height -
                160, width=210, height=150, mask='auto')
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, height - 50, "PERUSAHAAN DAERAH AIR MINUM TIRTA SATRIA")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(280, height - 70, "KABUPATEN BANYUMAS")
    c.setFont("Helvetica", 10)
    c.drawString(240, height - 100,
                 "Jl. Prof. Dr. Suharso No. 52 PURWOKERTO 53114")
    c.drawString(280, height - 120, "Telp. 0281-632324 Fax. 0281-641654")
    c.drawString(210, height - 140,
                 "Website: www.pdambanyumas.com E-mail: pdam_banyumas@yahoo.com")
    # draw line
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.5)
    c.line(30, height - 160, width - 30, height - 160)
    c.setFont("Courier-Bold", 12)
    c.drawString(250, height - 180, "SLIP GAJI PEGAWAI")
    c.setFont("Courier-Bold", 12)
    c.drawString(270, height - 200, "Januari 2025")

    c.setFont("Courier-Bold", 10)
    c.drawString(50, height - 220, "Nama")
    c.setFont("Courier", 10)
    c.drawString(110, height - 220, ": BAGUS SUDRAJAT, S.Kom.")
    c.setFont("Courier-Bold", 10)
    c.drawString(330, height - 220, "Golongan")
    c.setFont("Courier", 10)
    c.drawString(390, height - 220, ": B.2 - Pelaksana Muda Tk.I")
    c.setFont("Courier-Bold", 10)
    c.drawString(50, height - 240, "Nipam")
    c.setFont("Courier", 10)
    c.drawString(110, height - 240, ": 900800456")
    c.setFont("Courier-Bold", 10)
    c.drawString(330, height - 240, "Bank")
    c.setFont("Courier", 10)
    c.drawString(390, height - 240, ": - - -")
    c.setFont("Courier-Bold", 10)
    c.drawString(50, height - 260, "Jabatan")
    c.setFont("Courier", 10)
    c.drawString(110, height - 260, ": Staf Sub Bag. Teknologi Informasi")

    c.drawBoundary()

    # c.setFont("Helvetica-Bold", 12)
    # c.drawString(50, height - 280, "Penerimaan ( + )")
    # c.drawString(300, height - 280, "Potongan ( - )")
    # c.setFont("Helvetica", 12)

    # earnings = [
    #     ("Gaji Pokok", 2460100),
    #     ("Tunjangan Suami Istri", 246010),
    #     ("Tunjangan Anak", 123005),
    #     ("Tunjangan Jabatan", 275000),
    #     ("Tunjangan Beras", 450000),
    #     ("Tunjangan Kegiatan Kerja", 1775000),
    #     ("Tunjangan Air", 150000),
    #     ("Tunjangan Kesehatan", 0),
    #     ("Tunjangan PPh 21", 6013)
    # ]

    # deductions = [
    #     ("Iuran Pensiun", 110420),
    #     ("Potongan Astek", 71082),
    #     ("Potongan Sewa Rumah", 0),
    #     ("Potongan Jaminan Pensiun", 35541),
    #     ("Potongan BPJS Kes", 54791),
    #     ("Potongan TKK", 80500),
    #     ("Potongan Pajak PPh 21", 6013)
    # ]

    # y_position = height - 300
    # for earning, deduction in zip(earnings, deductions):
    #     c.drawString(50, y_position, f"{earning[0]}: Rp. {earning[1]:,}")
    #     c.drawString(300, y_position, f"{deduction[0]}: Rp. {deduction[1]:,}")
    #     y_position -= 20

    # total_earnings = sum(e[1] for e in earnings)
    # total_deductions = sum(d[1] for d in deductions)
    # net_salary = total_earnings - total_deductions

    # c.drawString(50, y_position - 20,
    #              f"Total Penerimaan: Rp. {total_earnings:,}")
    # c.drawString(300, y_position - 20,
    #              f"Total Potongan: Rp. {total_deductions:,}")
    # c.drawString(50, y_position - 40, f"Total Dibayarkan: Rp. {net_salary:,}")

    c.save()


if __name__ == "__main__":
    build()
