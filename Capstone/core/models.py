from django.db import models
from django.contrib.auth.models import User
from .choices import tipos

# Create your models here.
class Persona(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    edad = models.IntegerField()
    telefono = models.CharField(max_length=10)
    correo = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100,choices=tipos,default='R')
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Auto(models.Model):
    placa = models.CharField(max_length=10)
    marca = models.CharField(max_length=100)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.placa} {self.persona}"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    foto_perfil = models.ImageField(upload_to='perfil/', blank=True, null=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'
    
class RegistroEntradaSalida(models.Model):
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, null=True, blank=True)  # Puede ser una persona
    auto = models.ForeignKey(Auto, on_delete=models.CASCADE, null=True, blank=True)  # O un vehículo
    hora_entrada = models.DateTimeField()  # Hora de entrada
    hora_salida = models.DateTimeField(null=True, blank=True)  # Hora de salida (puede ser NULL)
    tipo_entrada = models.CharField(max_length=50, choices=[('P', 'Persona'), ('V', 'Vehículo')])  # Tipo de entrada

    def __str__(self):
        return f"Registro de {self.tipo_entrada} - {self.hora_entrada}"
