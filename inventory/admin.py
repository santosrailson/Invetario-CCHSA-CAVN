from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime
from unfold.admin import ModelAdmin, TabularInline
from import_export.admin import ImportExportModelAdmin

from .models import (
    Fabricante, Localizacao, Switch, PortaSwitch,
    Roteador, AccessPoint, Computador, EmailInstitucional,
    Site, Subrede, HistoricoPing,
)
from .actions import pingar_dispositivos, exportar_csv, gerar_pdf, compartilhar_whatsapp


# ─── Widget de senha com botão revelar ────────────────────────────────────────

class SenhaWidget(forms.TextInput):
    """Input tipo password com botão para revelar/ocultar."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["type"] = "password"
        self.attrs["autocomplete"] = "new-password"
        self.attrs["class"] = "vTextField"

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["type"] = "password"
        attrs["autocomplete"] = "new-password"
        attrs["id"] = attrs.get("id", f"id_{name}")
        field_id = attrs["id"]
        btn_id = f"btn_toggle_{name}"

        input_html = super().render(name, value, attrs, renderer)

        return format_html(
            """
            <div style="display:flex; align-items:center; gap:.5rem; max-width:500px;">
              {}
              <button type="button" id="{}"
                onclick="(function(){{
                  var f=document.getElementById('{}');
                  var b=document.getElementById('{}');
                  if(f.type==='password'){{f.type='text'; b.textContent='🙈 Ocultar';}}
                  else{{f.type='password'; b.textContent='👁 Mostrar';}}
                }})()"
                style="white-space:nowrap; padding:.35rem .8rem;
                       border:1px solid var(--border-color, #cbd5e1);
                       border-radius:6px;
                       background:var(--color-base-2, #f8fafc);
                       color:var(--color-on-base, #0f172a);
                       cursor:pointer; font-size:.82rem;">
                👁 Mostrar
              </button>
            </div>
            """,
            input_html, btn_id, field_id, btn_id,
        )


class SenhaField(forms.CharField):
    widget = SenhaWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("strip", False)
        super().__init__(*args, **kwargs)


# ─── Forms com campo senha customizado ────────────────────────────────────────

class EmailInstitucionalForm(forms.ModelForm):
    senha = SenhaField(label="Senha", help_text="Senha da conta de e-mail")

    class Meta:
        model = EmailInstitucional
        fields = "__all__"


class ComputadorForm(forms.ModelForm):
    senha = SenhaField(label="Senha", help_text="Senha de acesso ao sistema/computador")

    class Meta:
        model = Computador
        fields = "__all__"


class SiteForm(forms.ModelForm):
    senha = SenhaField(label="Senha", help_text="Senha para acesso ao site (opcional)")

    class Meta:
        model = Site
        fields = "__all__"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ip_link(ip, protocolo="http"):
    if not ip:
        return "—"
    return format_html(
        '<a href="{}://{}" target="_blank" rel="noopener">{} 🔗</a>',
        protocolo, ip, ip,
    )


def _ultimo_ping(dispositivo_tipo, obj_id):
    ping = (
        HistoricoPing.objects
        .filter(dispositivo_tipo=dispositivo_tipo, dispositivo_id=obj_id)
        .order_by("-timestamp")
        .first()
    )
    if not ping:
        return format_html('<span style="color:gray">—</span>')
    if ping.status == "ONLINE":
        latencia = f"{ping.latencia_ms:.1f} ms" if ping.latencia_ms else "online"
        return format_html(
            '🟢 <span style="color:green">{}</span>', latencia
        )
    return format_html('<span style="color:red">🔴 offline</span>')


# ─── Fabricante ───────────────────────────────────────────────────────────────

@admin.register(Fabricante)
class FabricanteAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = ["nome"]
    search_fields = ["nome"]


# ─── Localização ──────────────────────────────────────────────────────────────

@admin.register(Localizacao)
class LocalizacaoAdmin(ModelAdmin):
    list_display = ["__str__", "campus", "bloco", "andar", "sala", "rack"]
    list_filter = ["campus", "bloco"]
    search_fields = ["campus", "bloco", "sala", "rack"]
    fieldsets = [
        ("Identificação", {"fields": ["campus", "bloco"]}),
        ("Detalhe", {"fields": ["andar", "sala", "rack"]}),
    ]


# ─── Switch ───────────────────────────────────────────────────────────────────

class PortaSwitchInline(TabularInline):
    model = PortaSwitch
    extra = 0
    fields = ["numero", "velocidade", "vlan", "status", "dispositivo_conectado", "observacao"]


@admin.register(Switch)
class SwitchAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = [
        "nome", "ip_link", "modelo", "fabricante", "localizacao",
        "quantidade_portas", "ativo", "ultimo_ping",
    ]
    list_filter = ["ativo", "fabricante", "localizacao__bloco"]
    search_fields = ["nome", "ip", "numero_serie"]
    readonly_fields = ["ip_link", "criado_em", "atualizado_em"]
    inlines = [PortaSwitchInline]
    actions = [pingar_dispositivos, exportar_csv, gerar_pdf, compartilhar_whatsapp]
    fieldsets = [
        ("Identificação", {
            "fields": ["nome", "ip", "ip_link", "modelo", "fabricante", "numero_serie"],
        }),
        ("Localização", {
            "fields": ["localizacao"],
        }),
        ("Configuração", {
            "fields": ["quantidade_portas", "vlans", "ativo"],
        }),
        ("Observações", {
            "fields": ["tags", "observacoes"],
            "classes": ["collapse"],
        }),
        ("Registro", {
            "fields": ["criado_em", "atualizado_em"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="IP")
    def ip_link(self, obj):
        return _ip_link(obj.ip)

    @admin.display(description="Último Ping")
    def ultimo_ping(self, obj):
        return _ultimo_ping("switch", obj.pk)


# ─── Roteador ─────────────────────────────────────────────────────────────────

@admin.register(Roteador)
class RoteadorAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = [
        "nome", "ip_link", "modelo", "fabricante", "localizacao", "ativo", "ultimo_ping",
    ]
    list_filter = ["ativo", "fabricante", "localizacao__bloco"]
    search_fields = ["nome", "ip", "numero_serie"]
    readonly_fields = ["ip_link", "criado_em", "atualizado_em"]
    actions = [pingar_dispositivos, exportar_csv, gerar_pdf, compartilhar_whatsapp]
    fieldsets = [
        ("Identificação", {
            "fields": ["nome", "ip", "ip_link", "modelo", "fabricante", "numero_serie"],
        }),
        ("Localização", {"fields": ["localizacao"]}),
        ("Status", {"fields": ["ativo"]}),
        ("Observações", {
            "fields": ["tags", "observacoes"],
            "classes": ["collapse"],
        }),
        ("Registro", {
            "fields": ["criado_em", "atualizado_em"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="IP")
    def ip_link(self, obj):
        return _ip_link(obj.ip)

    @admin.display(description="Último Ping")
    def ultimo_ping(self, obj):
        return _ultimo_ping("roteador", obj.pk)


# ─── Access Point ─────────────────────────────────────────────────────────────

@admin.register(AccessPoint)
class AccessPointAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = [
        "nome", "ip_link", "ssid", "frequencia", "canal",
        "fabricante", "localizacao", "ativo", "ultimo_ping",
    ]
    list_filter = ["ativo", "fabricante", "frequencia", "localizacao__bloco"]
    search_fields = ["nome", "ip", "ssid"]
    readonly_fields = ["ip_link", "criado_em", "atualizado_em"]
    actions = [pingar_dispositivos, exportar_csv, gerar_pdf, compartilhar_whatsapp]
    fieldsets = [
        ("Identificação", {
            "fields": ["nome", "ip", "ip_link", "modelo", "fabricante"],
        }),
        ("Configuração Wi-Fi", {
            "fields": ["ssid", "canal", "frequencia"],
        }),
        ("Localização", {"fields": ["localizacao"]}),
        ("Status", {"fields": ["ativo"]}),
        ("Observações", {
            "fields": ["tags", "observacoes"],
            "classes": ["collapse"],
        }),
        ("Registro", {
            "fields": ["criado_em", "atualizado_em"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="IP")
    def ip_link(self, obj):
        return _ip_link(obj.ip)

    @admin.display(description="Último Ping")
    def ultimo_ping(self, obj):
        return _ultimo_ping("accesspoint", obj.pk)


# ─── Computador ───────────────────────────────────────────────────────────────

@admin.register(Computador)
class ComputadorAdmin(ModelAdmin, ImportExportModelAdmin):
    form = ComputadorForm
    list_display = [
        "nome", "hostname", "ip", "sistema_operacional",
        "usuario_responsavel", "departamento", "localizacao", "ativo",
    ]
    list_filter = ["ativo", "sistema_operacional", "departamento", "localizacao__bloco"]
    search_fields = ["nome", "hostname", "ip", "mac", "usuario_responsavel"]
    readonly_fields = ["criado_em", "atualizado_em"]
    actions = [pingar_dispositivos, exportar_csv, gerar_pdf, compartilhar_whatsapp]
    fieldsets = [
        ("Identificação", {
            "fields": ["nome", "hostname", "ip", "mac"],
        }),
        ("Software", {
            "fields": ["sistema_operacional"],
        }),
        ("Acesso", {
            "fields": ["usuario_responsavel", "senha"],
        }),
        ("Responsabilidade", {
            "fields": ["departamento"],
        }),
        ("Localização", {"fields": ["localizacao"]}),
        ("Status", {"fields": ["ativo"]}),
        ("Observações", {
            "fields": ["tags", "observacoes"],
            "classes": ["collapse"],
        }),
        ("Registro", {
            "fields": ["criado_em", "atualizado_em"],
            "classes": ["collapse"],
        }),
    ]


# ─── E-mail Institucional ─────────────────────────────────────────────────────

@admin.register(EmailInstitucional)
class EmailInstitucionalAdmin(ModelAdmin, ImportExportModelAdmin):
    form = EmailInstitucionalForm
    list_display = [
        "endereco", "usuario", "departamento",
        "servidor_email", "cota_mb", "ativo",
    ]
    list_filter = ["ativo", "departamento", "servidor_email"]
    search_fields = ["endereco", "usuario", "departamento"]
    readonly_fields = ["email_link", "criado_em", "atualizado_em"]
    actions = [exportar_csv, gerar_pdf, compartilhar_whatsapp]
    fieldsets = [
        ("Conta", {
            "fields": ["endereco", "email_link", "usuario", "senha", "departamento"],
        }),
        ("Servidor", {
            "fields": ["servidor_email", "cota_mb"],
        }),
        ("Status", {"fields": ["ativo"]}),
        ("Observações", {
            "fields": ["tags", "observacoes"],
            "classes": ["collapse"],
        }),
        ("Registro", {
            "fields": ["criado_em", "atualizado_em"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="Endereço")
    def email_link(self, obj):
        return format_html(
            '<a href="mailto:{}">{}</a>', obj.endereco, obj.endereco
        )


# ─── Site ─────────────────────────────────────────────────────────────────────

@admin.register(Site)
class SiteAdmin(ModelAdmin, ImportExportModelAdmin):
    form = SiteForm
    list_display = [
        "nome", "url_link", "ip_servidor", "responsavel",
        "certificado_expiracao", "ativo",
    ]
    list_filter = ["ativo"]
    search_fields = ["nome", "url", "ip_servidor", "responsavel"]
    readonly_fields = ["url_link", "criado_em", "atualizado_em"]
    actions = [exportar_csv, gerar_pdf, compartilhar_whatsapp]
    fieldsets = [
        ("Identificação", {
            "fields": ["nome", "url", "url_link", "ip_servidor"],
        }),
        ("Responsabilidade", {
            "fields": ["responsavel", "certificado_expiracao"],
        }),
        ("Credenciais", {
            "fields": ["usuario", "senha"],
            "classes": ["collapse"],
            "description": "Preencha apenas se o site exigir autenticação.",
        }),
        ("Status", {"fields": ["ativo"]}),
        ("Observações", {
            "fields": ["tags", "observacoes"],
            "classes": ["collapse"],
        }),
        ("Registro", {
            "fields": ["criado_em", "atualizado_em"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="URL")
    def url_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{} 🔗</a>',
            obj.url, obj.url,
        )


# ─── Subrede ──────────────────────────────────────────────────────────────────

@admin.register(Subrede)
class SubredeAdmin(ModelAdmin, ImportExportModelAdmin):
    list_display = [
        "cidr", "gateway", "vlan", "finalidade",
        "faixa_inicio", "faixa_fim", "total_ips_display",
    ]
    search_fields = ["cidr", "vlan", "finalidade"]
    fieldsets = [
        ("Rede", {
            "fields": ["cidr", "gateway", "vlan", "finalidade"],
        }),
        ("Faixa de IPs", {
            "fields": ["faixa_inicio", "faixa_fim"],
        }),
        ("Observações", {
            "fields": ["observacoes"],
            "classes": ["collapse"],
        }),
    ]

    @admin.display(description="Total de IPs")
    def total_ips_display(self, obj):
        total = obj.total_ips()
        return f"{total:,}".replace(",", ".")


# ─── Histórico de Ping ────────────────────────────────────────────────────────

@admin.register(HistoricoPing)
class HistoricoPingAdmin(ModelAdmin):
    list_display = [
        "ip", "dispositivo_tipo", "status_display",
        "latencia_ms", "mac_address", "fabricante_mac", "timestamp",
    ]
    list_filter = ["status", "dispositivo_tipo"]
    search_fields = ["ip", "dispositivo_tipo", "mac_address", "fabricante_mac"]
    readonly_fields = [
        "ip", "dispositivo_tipo", "dispositivo_id",
        "status", "latencia_ms", "mac_address", "fabricante_mac", "timestamp",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Status")
    def status_display(self, obj):
        if obj.status == "ONLINE":
            return format_html('<span style="color:green">🟢 Online</span>')
        return format_html('<span style="color:red">🔴 Offline</span>')
