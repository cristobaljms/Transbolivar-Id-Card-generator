from django.shortcuts import render
from django.templatetags.static import static
from django.db import connection
from collections import namedtuple
from wand.image import Image, Color
import os

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
        url_diseno_carnet = static('files/carnet.pdf')
        url_output = static('files/')
        pdf_to_jpg(url_diseno_carnet, url_output)
    return render(request, 'empleados/generar_carnet.html', contexto)



def pdf_to_jpg(pdf_path,  output_path = None, resolution = 200):
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

