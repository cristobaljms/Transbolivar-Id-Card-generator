from django.shortcuts import render

from django.db import connection
from collections import namedtuple



# Create your views here.
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
