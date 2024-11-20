from django import forms
from .models import Persona, Auto

class PersonaForm(forms.ModelForm):
    class Meta:
        model = Persona
        fields = ['nombre', 'apellido', 'edad', 'telefono', 'correo', 'direccion', 'tipo', 'activo']
        
class AutoForm(forms.ModelForm):
    class Meta:
        model = Auto
        fields = ['placa', 'marca', 'persona']
        
class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="Sube tu archivo Excel", widget=forms.FileInput(attrs={'accept': '.xls,.xlsx'}))

