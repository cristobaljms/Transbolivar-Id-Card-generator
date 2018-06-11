import os
import io
import qrcode
from django.shortcuts import render
from django.templatetags.static import static
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from django.db import connection
from collections import namedtuple
from reportlab.pdfgen import canvas
from wand.image import Image, Color
from ROOT import settings
from django.http import HttpResponse

def index(request):
    query = "SELECT * FROM empleados"
    #query = "SELECT DISTINCT(a.cedper) AS cedula, (a.apeper || ' ' || a.nomper) as nombres, d.descar as descripcion FROM sno_personal a INNER JOIN sno_hpersonalnomina b ON a.codper = b.codper INNER JOIN sno_cargo d ON b.codcar = d.codcar WHERE b.codperi = ( SELECT MAX(codperi) FROM sno_hpersonalnomina c WHERE  b.codper = c.codper) ORDER BY a.cedper"
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
    query = "SELECT * FROM empleados WHERE cedula = %s"
    #query = "SELECT DISTINCT(a.cedper) AS cedula, (a.apeper || ' ' || a.nomper) as nombres, d.descar as descripcion FROM sno_personal a INNER JOIN sno_hpersonalnomina b ON a.codper = b.codper INNER JOIN sno_cargo d ON b.codcar = d.codcar WHERE b.codperi = ( SELECT MAX(codperi) FROM sno_hpersonalnomina c WHERE  b.codper = c.codper) AND a.cedper = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, [str(id)])
        result = namedtuplefetchall(cursor)
        contexto = {'cedula':result[0].cedula, 'nombres':result[0].nombres, 'cargo': result[0].cargo}
        cargos_operaciones = ['OPERADOR URBANO','OPERADOR INTERURBANO','OPERADOR INTERURBANO I', 'OPERADOR INSTRUCTOR', 'SUPERVISOR DE OPERACIONES','JEFE DEL CENTRO DE CONTROL DE OPERACIONES','AUXILIAR DE FLOTA']
        # Generar imagen JPG desde el PDF creado
        url_diseno_carnet_admin = os.path.join(settings.BASE_DIR, 'static/files/carnet_admin.pdf')
        url_diseno_carnet_oper = os.path.join(settings.BASE_DIR, 'static/files/carnet_oper.pdf')
        url_carnet = os.path.join(settings.BASE_DIR, 'static/files/tmp/'+result[0].cedula+'-0.pdf')
        url_carnet_final = os.path.join(settings.BASE_DIR, 'static/files/carnets/')
        url_output = os.path.join(settings.BASE_DIR, 'static/files/')

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(153,240))
        
        foto_carnet = os.path.join(settings.BASE_DIR, 'static/img/foto_carnet.png')
        if os.path.exists(os.path.join(settings.BASE_DIR, 'static/img/'+result[0].cedula+'.jpeg')):
            foto_carnet = os.path.join(settings.BASE_DIR, 'static/img/'+result[0].cedula+'.jpeg')
        
        can.drawImage(foto_carnet, 40, 88, width=72, height=72, mask=None)

        can.setFont("Helvetica-Bold", 6)
        if len(result[0].nombres) > 36:
            can.setFont("Helvetica-Bold", 5.5)
        can.drawCentredString(76.5, 80, result[0].nombres)

        can.setFont("Helvetica", 6)
        can.drawCentredString(76.5, 73, 'C.I '+result[0].cedula)


        can.setFont("Helvetica-Bold", 8)
        if len(result[0].cargo) > 30:
            can.setFont("Helvetica-Bold", 7.5)
        if len(result[0].cargo) > 33:
            can.setFont("Helvetica-Bold", 6.6)
        if len(result[0].cargo) > 35:
            can.setFont("Helvetica-Bold", 6)

        #can.drawCentredString(76.5, 62, str(len(result[0].cargo)))
        can.drawCentredString(76.5, 52, result[0].cargo)
        can.save()

        packet.seek(0)

        new_pdf = PdfFileReader(packet)

        existing_pdf = PdfFileReader(open(url_diseno_carnet_admin, "rb"))
        if result[0].cargo in cargos_operaciones:
            existing_pdf = PdfFileReader(open(url_diseno_carnet_oper, "rb"))
        
        output = PdfFileWriter()
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

        # finally, write "output" to a real file
        outputStream = open(url_carnet, "wb")
        output.write(outputStream)
        outputStream.close()

        url_carnet_cara2 = generar_carnet_cara2(result[0].cedula)

        merger = PdfFileMerger()
        
        merger.append(PdfFileReader(open(url_carnet, 'rb')))
        merger.append(PdfFileReader(open(url_carnet_cara2, 'rb')))

        merger.write(url_carnet_final+result[0].cedula+'.pdf')

        pdf_to_jpg(url_carnet,url_output,200,'cara_1')

    return render(request, 'empleados/generar_carnet.html', contexto)


def generar_carnet_cara2(ci):
    path_diseno_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnet_admin.pdf')
    url_carnet = os.path.join(settings.BASE_DIR, 'static/files/tmp/'+ci+'-1.pdf')
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
    canqr.drawImage(url_qrcode_img, 85, 4, width=64, height=64, mask=None)
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

    pdf_to_jpg(url_carnet,url_output,200,'cara_2')

    return url_carnet



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
                image_name = os.path.join(output_path, name_file+'.jpg')
                image.save(filename = image_name)

def renderizar(request):

    cedula = request.POST['cedula']
    nombres = request.POST['nombres']
    cargo = request.POST['cargo']
    

    # Generar imagen JPG desde el PDF creado
    url_diseno_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnet_admin.pdf')
    url_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnets/'+cedula+'-0.pdf')
    url_output = os.path.join(settings.BASE_DIR, 'static/files/')

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(153,240))
       
    foto_carnet = os.path.join(settings.BASE_DIR, 'static/files/qrimg/foto_carnet.png')
    can.drawImage(foto_carnet, 40, 88, width=72, height=72, mask=None)

    can.setFont("Helvetica-Bold", 6)
    if len(nombres) > 36:
        can.setFont("Helvetica-Bold", 5.5)
    can.drawCentredString(76.5, 80, nombres)

    can.setFont("Helvetica", 6)
    can.drawCentredString(76.5, 73, 'C.I '+cedula)

    can.setFont("Helvetica-Bold", 8)
    if len(cargo) > 30:
        can.setFont("Helvetica-Bold", 7.5)
    if len(cargo) > 33:
        can.setFont("Helvetica-Bold", 6.6)
    if len(cargo) > 35:
        can.setFont("Helvetica-Bold", 6)

    #can.drawCentredString(76.5, 62, str(len(cargo)))
    can.drawCentredString(76.5, 52, cargo)
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

    generar_carnet_cara2(cedula)
    pdf_to_jpg(url_carnet,url_output,200,'cara_1')    
    contexto = {'cedula':cedula, 'nombres':nombres, 'cargo': cargo}    
    return render(request, 'empleados/generar_carnet.html', contexto)


def imprimir(request, cedula):
    url_carnet = os.path.join(settings.BASE_DIR, 'static/files/carnets/'+str(cedula)+'.pdf')
    image_data = open(url_carnet, "rb").read()
    return HttpResponse(image_data, content_type='application/pdf')    