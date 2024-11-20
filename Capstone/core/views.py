from django.shortcuts import render, redirect, get_object_or_404
from core.utils.videoReconocer import   generate_frames, last_detected_plate
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import Persona, Auto, RegistroEntradaSalida
from django.http import StreamingHttpResponse
from .forms import PersonaForm, AutoForm
from django.http import JsonResponse
from .forms import ExcelUploadForm
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from django.utils import timezone
from io import BytesIO
import base64

@login_required
def main(request):
    tipo_filtro = request.GET.get('tipo', '')  # Obtener el valor del filtro
    
    # Aplicar el filtro según el tipo seleccionado
    if tipo_filtro == 'R':
        residentes = Persona.objects.filter(tipo='R')
    elif tipo_filtro == 'V':
        residentes = Persona.objects.filter(tipo='V')
    else:
        residentes = Persona.objects.all()  # Mostrar todos si no hay filtro

    autos = Auto.objects.all()
    return render(request, 'main.html', {'residentes': residentes, 'autos': autos})

@login_required
def perfil(request):
    usuario = request.user
    return render(request, 'perfil.html', {'usuario': usuario})

@login_required
def residentes(request):
    residentes = Persona.objects.all()
    return render(request, 'residentes.html', {'residentes': residentes})

@login_required
def crear_auto(request):
    if request.method == 'GET':
        return render(request, 'crearAuto.html', {
            'form': AutoForm
        })
    else:
        try:
            form = AutoForm(request.POST)
            new_auto = form.save(commit=False)
            new_auto.user = request.user
            new_auto.save()
            return redirect('autos')
        except ValueError:
            return render(request, 'crearAuto.html', {
                'form': AutoForm,
                'error':'Porfavor ingresar datos validos'
            })

@login_required
def crear_residente(request):
    if request.method == 'GET':
        return render(request, 'crearResidente.html', {
            'form': PersonaForm
        })
    else:
        try:
            form = PersonaForm(request.POST)
            new_residente = form.save(commit=False)
            new_residente.user = request.user
            new_residente.save()
            return redirect('Residentes')
        except ValueError:
            return render(request, 'crearResidente.html', {
                'form': PersonaForm,
                'error':'Porfavor ingresar datos validos'
            })

@login_required
def edicion_auto(request, id):
    if request.method == 'GET':
        detalle = get_object_or_404(Auto, pk=id)
        form = AutoForm(instance=detalle)
        return render(request, 'editarAuto.html', {'detalle': detalle, 'form': form})
    else:
        try:
            detalle = get_object_or_404(Auto, pk=id)
            form = AutoForm(request.POST, instance=detalle)
            form.save()
            return redirect ('autos')
        except:
            return render (request, 'editarAuto.html', {'detalle': detalle, 'form': form, 
                                                             'error': "Error actualizando datos"})

@login_required
def edicion_residente(request, id):
    if request.method == 'GET':
        detalle = get_object_or_404(Persona, pk=id)
        form = PersonaForm(instance=detalle)
        return render(request, 'editarResidente.html', {'detalle': detalle, 'form': form})
    else:
        try:
            detalle = get_object_or_404(Persona, pk=id)
            form = PersonaForm(request.POST, instance=detalle)
            form.save()
            return redirect ('Residentes')
        except:
            return render (request, 'editarResidente.html', {'detalle': detalle, 'form': form, 
                                                             'error': "Error actualizando datos"})

@login_required
def eliminar_auto(request, id):
    auto = Auto.objects.get(id=id)
    auto.delete()
    
    return redirect('autos')

@login_required
def eliminar_residente(request, id):
    residente = Persona.objects.get(id=id)
    residente.delete()
    
    return redirect('Residentes')

@login_required
def autos(request):
    autos = Auto.objects.all()
    return render(request, 'autos.html', {'autos': autos})

@login_required
def video_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def inicioSesion(request):
    if request.method == 'GET':
        return render(request, 'login.html',{
            'form': AuthenticationForm
        })
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        
        if user is None:
            return render(request, 'login.html',{
                'form': AuthenticationForm,
                'error': 'Usuario o password esta incorrecto'
        })
        else:
            login(request, user)
            return redirect('Pagina Principal')

@login_required      
def cerrarSesion(request):
    logout(request)
    return redirect('/')

def verificar_patente_detectada(request):
    return JsonResponse(last_detected_plate)

def reconocedor(request):
    return render(request, 'reconocedor.html')

def informes(request):
    # Obtener la fecha del parámetro GET, si existe
    fecha_dia_param = request.GET.get('fecha_dia')
    
    # Si no se especifica fecha, tomamos la fecha de hoy
    if fecha_dia_param is None:
        fecha_dia = timezone.localtime(timezone.now()).date()  # Asegura la zona horaria local
    else:
        try:
            fecha_dia = datetime.strptime(fecha_dia_param, '%Y-%m-%d').date()
        except ValueError:
            return render(request, 'informes.html', {
                'error': 'Fecha inválida. Utiliza el formato YYYY-MM-DD.',
            })

    # Parte 1: Generación del Histograma de Ingresos por Hora
    registros = RegistroEntradaSalida.objects.filter(
        hora_entrada__date=fecha_dia,
        tipo_entrada='V'  # Solo registros de vehículos
    ).values('hora_entrada')

    # Convertimos los datos a un DataFrame
    df = pd.DataFrame(list(registros))
    
    if not df.empty:
        df['hora_entrada'] = df['hora_entrada'].apply(lambda x: timezone.localtime(x))  # Convierte UTC a local
        df['hora'] = df['hora_entrada'].dt.hour

        frecuencia_por_hora = df['hora'].value_counts().reindex(range(6, 30), fill_value=0).sort_index()

        # Gráfico con barras juntas
        plt.figure(figsize=(12, 6))
        
        # Dibujar el histograma con barras juntas
        plt.bar(frecuencia_por_hora.index, frecuencia_por_hora.values, color='skyblue', edgecolor='black', width=0.9)
        
        plt.title(f"Frecuencia de Ingreso de Autos por Hora - {fecha_dia}")
        plt.xlabel("Hora del Día")
        plt.ylabel("Cantidad de Ingresos")
        plt.xticks(range(6, 30), labels=[f"{h % 24}:00" for h in range(6, 30)], rotation=45)

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        graphic = base64.b64encode(image_png).decode('utf-8')
        plt.close()
    else:
        graphic = None

    # Parte 2: Obtención de las Tablas de Visitas Activas e Inactivas
    visitas_activas = Persona.objects.filter(tipo='V', activo=True)
    visitas_inactivas = Persona.objects.filter(tipo='V', activo=False)

    # Parte 3: Contexto y Renderización
    context = {
        'graphic': graphic,
        'fecha_dia': fecha_dia,
        'visitas_activas': visitas_activas,
        'visitas_inactivas': visitas_inactivas,
    }
    return render(request, 'informes.html', context)


def upload_excel(request):
    if request.method == "POST":
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            try:
                # Leer el archivo Excel
                data = pd.read_excel(file)

                # Validar que las columnas requeridas estén presentes
                required_columns = ['persona', 'auto', 'hora_entrada', 'hora_salida', 'tipo_entrada']
                if not all(col in data.columns for col in required_columns):
                    raise ValueError("El archivo debe contener las columnas: persona, auto, hora_entrada, hora_salida, tipo_entrada.")

                # Crear registros
                registros = []
                for _, row in data.iterrows():
                    # Obtener los objetos relacionados (persona y auto)
                    persona = Persona.objects.filter(id=row['persona']).first() if pd.notna(row['persona']) else None
                    auto = Auto.objects.filter(id=row['auto']).first() if pd.notna(row['auto']) else None

                    # Validar tipo de entrada
                    if row['tipo_entrada'] not in ['P', 'V']:
                        raise ValueError(f"Tipo de entrada inválido: {row['tipo_entrada']} en la fila {_ + 1}.")

                    # Crear el registro
                    registro = RegistroEntradaSalida(
                        persona=persona,
                        auto=auto,
                        hora_entrada=row['hora_entrada'],
                        hora_salida=row['hora_salida'] if pd.notna(row['hora_salida']) else None,
                        tipo_entrada=row['tipo_entrada']
                    )
                    registros.append(registro)

                # Guardar todos los registros en la base de datos
                RegistroEntradaSalida.objects.bulk_create(registros)

                return render(request, 'success.html', {'message': 'Registros subidos exitosamente!'})

            except Exception as e:
                return render(request, 'error.html', {'error': str(e)})

    else:
        form = ExcelUploadForm()

    return render(request, 'upload_excel.html', {'form': form})
