from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime
from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin

from .models import (
    Fabricante, Localizacao, Switch, PortaSwitch,
    Roteador, AccessPoint, Computador, EmailInstitucional,
    Site, Subrede, HistoricoPing, Impressora,
)
from .actions import pingar_dispositivos, exportar_csv, gerar_pdf, compartilhar_whatsapp


# ─── Widget de senha com botão revelar ────────────────────────────────────────

class SenhaWidget(forms.TextInput):
    """Input tipo password com botão para revelar/ocultar."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["type"] = "password"
        self.attrs["autocomplete"] = "new-password"