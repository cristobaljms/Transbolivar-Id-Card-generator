import os
import io
import qrcode
from django.shortcuts import render
from django.templatetags.static import static
from PyPDF2 import PdfFileWriter, PdfFileReader
from django.db import connection
from collections import namedtuple
from reportlab.pdfgen import canvas
from wand.image import Image, Color
from ROOT import settings

def index(request):
    query = "SELECT DISTINCT(a.cedper) AS cedula, (a.apeper || ' ' || a.nomper) as nombres, d.descar as descripcion FROM sno_personal a INNER JOIN sno_hpersonalnomina b ON a.codper = b.codper INNER JOIN sno_cargo d ON b.codcar = d.codcar WHERE b.codperi = ( SELECT MAX(codperi) FROM sno_hpersonalnomina c WHERE  b.codper = c.codper) ORDER BY a.cedper"
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = namedtuplefetchall(cursor)
        contexto = {'empleados':results}
    return render(request,"base/base.html", contexto)


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def generar_carnet(request, id):
    query = "SELECT DISTINCT(a.cedper) AS cedula, (a.apeper || ' ' || a.nomper) as nombres, d.descar as descripcion FROM sno_personal a INNER JOIN sno_hpersonalnomina b ON a.codper = b.codper INNER JOIN sno_cargo d ON b.codcar = d.codcar WHERE b.codperi = ( SELECT MAX(codperi) FROM sno_hpersonalnomina c WHERE  b.codper = c.codper) AND a.cedper = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, [str(id)])
        result = namedtuplefetchall(cursor)
        contexto = {'cedula':result[0].cedula, 'nombres':result[0].nombres, 'descripcion': result[0].descripcion}

        # Generar imagen JPG desde el PDF creado
        url_diseno_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnet.pdf')
        url_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnets/'+result[0].cedula+'-0.pdf')
        url_output = os.path.join(settings.BASE_DIR, 'static/files/')

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(153,240))
        
        can.drawString(10, 100, result[0].cedula)
        can.drawString(10, 110, result[0].nombres)
        can.drawString(10, 120, result[0].descripcion)
        can.save()

        packet.seek(0)

        new_pdf = PdfFileReader(packet)

        # read your existing PDF
        existing_pdf = PdfFileReader(open(url_diseno_carnet, "rb"))
        output = PdfFileWriter()
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

        # finally, write "output" to a real file
        outputStream = open(url_carnet, "wb")
        output.write(outputStream)
        outputStream.close()

        generar_carnet_cara2(result[0].cedula)
        pdf_to_jpg(url_carnet,url_output,200,result[0].cedula+'-0')

    return render(request, 'empleados/generar_carnet.html', contexto)


def generar_carnet_cara2(ci):

    path_diseno_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnet.pdf')
    url_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnets/'+ci+'-1.pdf')
    url_output = os.path.join(settings.BASE_DIR, 'static/files/')

    qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=1,
        )

    qr.add_data(ci)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    path_qrcode = os.path.join(settings.BASE_DIR, 'static/files/qrimg/')
    f = open(path_qrcode+ci+".png", "wb")
    img.save(f)
    f.close()

    packet = io.BytesIO()
    canqr = canvas.Canvas(packet, pagesize=(153,240))
    url_qrcode_img = os.path.join(settings.BASE_DIR, 'static/files/qrimg/'+ci+'.png')
    canqr.drawImage(url_qrcode_img, 10, 5, width=50, height=50, mask=None)
    canqr.save()

    packet.seek(0)

    new_pdf = PdfFileReader(packet)

    # read your existing PDF
    existing_pdf = PdfFileReader(open(path_diseno_carnet, "rb"))
    output = PdfFileWriter()
    page = existing_pdf.getPage(1)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    

    # finally, write "output" to a real file
    outputStream = open(url_carnet, "wb")
    output.write(outputStream)
    outputStream.close()

    pdf_to_jpg(url_carnet,url_output,200,ci+'-1')


def pdf_to_jpg(pdf_path = None,  output_path = None, resolution = 200, name_file = 'file'):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    if not output_path:
        output_path = os.path.dirname(pdf_path)

    with Image(filename=pdf_path, resolution=resolution) as  pdf:
        for n, page in enumerate(pdf.sequence):
            with Image(page) as image:
                image.format = 'jpg'
                image.background_color = Color('white')
                image.alpha_channel = 'remove'
                image_name = os.path.join(output_path, '{}-{}.jpg'.format(pdf_name, n))
                image.save(filename = image_name)