from django.db import models
from django.utils import timezone


class Fabricante(models.Model):
    nome = models.CharField("Nome", max_length=100, unique=True)

    class Meta:
        verbose_name = "Fabricante"
        verbose_name_plural = "Fabricantes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Localizacao(models.Model):
    campus = models.CharField("Campus", max_length=100)
    bloco = models.CharField("Bloco", max_length=50)
    andar = models.CharField("Andar", max_length=20, blank=True)
    sala = models.CharField("Sala", max_length=50, blank=True)
    rack = models.CharField("Rack", max_length=50, blank=True)

    class Meta:
        verbose_name = "Localização"
        verbose_name_plural = "Localizações"
        ordering = ["campus", "bloco", "sala"]

    def __str__(self):
        partes = [self.campus, f"Bloco {self.bloco}"]
        if self.andar:
            partes.append(f"{self.andar}° andar")
        if self.sala:
            partes.append(f"Sala {self.sala}")
        if self.rack:
            partes.append(f"Rack {self.rack}")
        return " › ".join(partes)


class Switch(models.Model):
    nome = models.CharField("Nome", max_length=100)
    ip = models.GenericIPAddressField("Endereço IP", protocol="both")
    modelo = models.CharField("Modelo", max_length=100)
    fabricante = models.ForeignKey(
        Fabricante, on_delete=models.PROTECT, verbose_name="Fabricante"
    )
    numero_serie = models.CharField("Número de Série", max_length=100, blank=True)
    quantidade_portas = models.PositiveIntegerField("Qtd. de Portas", default=24)
    localizacao = models.ForeignKey(
        Localizacao, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Localização"
    )
    vlans = models.CharField("VLANs", max_length=255, blank=True,
                             help_text="Ex: 1,10,20,100")
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True,
                            help_text="Separadas por vírgula")
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Switch"
        verbose_name_plural = "Switches"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.ip})"


class PortaSwitch(models.Model):
    VELOCIDADE_CHOICES = [
        ("10M", "10 Mbps"),
        ("100M", "100 Mbps"),
        ("1G", "1 Gbps"),
        ("10G", "10 Gbps"),
    ]
    STATUS_CHOICES = [
        ("ATIVA", "Ativa"),
        ("INATIVA", "Inativa"),
        ("ERRO", "Erro"),
    ]

    switch = models.ForeignKey(
        Switch, on_delete=models.CASCADE, related_name="portas", verbose_name="Switch"
    )
    numero = models.PositiveIntegerField("Número da Porta")
    velocidade = models.CharField(
        "Velocidade", max_length=10, choices=VELOCIDADE_CHOICES, default="1G"
    )
    vlan = models.CharField("VLAN", max_length=20, blank=True)
    status = models.CharField(
        "Status", max_length=10, choices=STATUS_CHOICES, default="INATIVA"
    )
    dispositivo_conectado = models.CharField(
        "Dispositivo Conectado", max_length=150, blank=True
    )
    observacao = models.CharField("Observação", max_length=255, blank=True)

    class Meta:
        verbose_name = "Porta de Switch"
        verbose_name_plural = "Portas de Switch"
        ordering = ["switch", "numero"]
        unique_together = [["switch", "numero"]]

    def __str__(self):
        return f"{self.switch.nome} — Porta {self.numero}"


class Roteador(models.Model):
    nome = models.CharField("Nome", max_length=100)
    ip = models.GenericIPAddressField("Endereço IP", protocol="both")
    modelo = models.CharField("Modelo", max_length=100)
    fabricante = models.ForeignKey(
        Fabricante, on_delete=models.PROTECT, verbose_name="Fabricante"
    )
    numero_serie = models.CharField("Número de Série", max_length=100, blank=True)
    localizacao = models.ForeignKey(
        Localizacao, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Localização"
    )
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Roteador"
        verbose_name_plural = "Roteadores"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.ip})"


class AccessPoint(models.Model):
    FREQUENCIA_CHOICES = [
        ("2.4GHz", "2.4 GHz"),
        ("5GHz", "5 GHz"),
        ("Dual", "Dual Band"),
    ]

    nome = models.CharField("Nome", max_length=100)
    ip = models.GenericIPAddressField("Endereço IP", protocol="both")
    modelo = models.CharField("Modelo", max_length=100)
    fabricante = models.ForeignKey(
        Fabricante, on_delete=models.PROTECT, verbose_name="Fabricante"
    )
    ssid = models.CharField("SSID", max_length=100, blank=True)
    canal = models.PositiveIntegerField("Canal", null=True, blank=True)
    frequencia = models.CharField(
        "Frequência", max_length=10, choices=FREQUENCIA_CHOICES, default="Dual"
    )
    localizacao = models.ForeignKey(
        Localizacao, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Localização"
    )
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Access Point"
        verbose_name_plural = "Access Points"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.ip})"


class Computador(models.Model):
    nome = models.CharField("Nome", max_length=100)
    hostname = models.CharField("Hostname", max_length=100, blank=True)
    ip = models.GenericIPAddressField("Endereço IP", protocol="both", null=True, blank=True)
    mac = models.CharField("MAC Address", max_length=17, blank=True,
                           help_text="Ex: AA:BB:CC:DD:EE:FF")
    sistema_operacional = models.CharField("Sistema Operacional", max_length=100, blank=True)
    usuario_responsavel = models.CharField("Usuário Responsável", max_length=150, blank=True)
    senha = models.CharField("Senha", max_length=255, blank=True,
                             help_text="Senha de acesso ao sistema/computador")
    departamento = models.CharField("Departamento", max_length=100, blank=True)
    localizacao = models.ForeignKey(
        Localizacao, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Localização"
    )
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Computador"
        verbose_name_plural = "Computadores"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.hostname or self.ip})"


class EmailInstitucional(models.Model):
    endereco = models.EmailField("Endereço de E-mail", unique=True)
    usuario = models.CharField("Usuário", max_length=150)
    senha = models.CharField("Senha", max_length=255, blank=True,
                             help_text="Senha da conta de e-mail")
    departamento = models.CharField("Departamento", max_length=100, blank=True)
    servidor_email = models.CharField("Servidor de E-mail", max_length=100, blank=True)
    cota_mb = models.IntegerField("Cota (MB)", null=True, blank=True)
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "E-mail Institucional"
        verbose_name_plural = "E-mails Institucionais"
        ordering = ["endereco"]

    def __str__(self):
        return self.endereco


class Site(models.Model):
    nome = models.CharField("Nome", max_length=100)
    url = models.URLField("URL", max_length=255)
    ip_servidor = models.GenericIPAddressField(
        "IP do Servidor", protocol="both", null=True, blank=True
    )
    responsavel = models.CharField("Responsável", max_length=150, blank=True)
    certificado_expiracao = models.DateField(
        "Validade do Certificado SSL", null=True, blank=True
    )
    usuario = models.CharField(
        "Usuário", max_length=150, blank=True,
        help_text="Usuário para acesso ao site (opcional)"
    )
    senha = models.CharField(
        "Senha", max_length=255, blank=True,
        help_text="Senha para acesso ao site (opcional)"
    )
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True)
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.url})"


class Subrede(models.Model):
    cidr = models.CharField("CIDR", max_length=18, unique=True,
                            help_text="Ex: 192.168.1.0/24")
    gateway = models.GenericIPAddressField("Gateway", protocol="both", null=True, blank=True)
    vlan = models.CharField("VLAN", max_length=20, blank=True)
    finalidade = models.CharField("Finalidade", max_length=150, blank=True)
    faixa_inicio = models.GenericIPAddressField(
        "Início da Faixa", protocol="both", null=True, blank=True
    )
    faixa_fim = models.GenericIPAddressField(
        "Fim da Faixa", protocol="both", null=True, blank=True
    )
    observacoes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Subrede"
        verbose_name_plural = "Subredes"
        ordering = ["cidr"]

    def __str__(self):
        return self.cidr

    def total_ips(self):
        """Calcula o total de IPs na subrede a partir do CIDR."""
        try:
            prefixo = int(self.cidr.split("/")[1])
            return 2 ** (32 - prefixo)
        except (IndexError, ValueError):
            return 0


class HistoricoPing(models.Model):
    STATUS_CHOICES = [
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
    ]

    dispositivo_tipo = models.CharField("Tipo de Dispositivo", max_length=50)
    dispositivo_id = models.PositiveIntegerField("ID do Dispositivo", null=True, blank=True)
    ip = models.GenericIPAddressField("Endereço IP", protocol="both")
    status = models.CharField("Status", max_length=10, choices=STATUS_CHOICES)
    latencia_ms = models.FloatField("Latência (ms)", null=True, blank=True)
    mac_address = models.CharField("MAC Address", max_length=17, blank=True, default="")
    fabricante_mac = models.CharField("Fabricante (MAC)", max_length=255, blank=True, default="")
    timestamp = models.DateTimeField("Timestamp", auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de Ping"
        verbose_name_plural = "Histórico de Pings"
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.ip} — {self.status} "
            f"({self.timestamp.strftime('%d/%m/%Y %H:%M')})"
        )
 
 
class Impressora(models.Model): 
class Impressora(models.Model):
    TIPO_CHOICES = [
        ("LASER", "Laser"),
        ("JATO_TINTA", "Jato de Tinta"),
        ("MULTIFUNCIONAL", "Multifuncional"),
        ("MATRICIAL", "Matricial"),
        ("TERMICA", "Térmica"),
        ("OUTRO", "Outro"),
    ]

    CONEXAO_CHOICES = [
        ("USB", "USB"),
        ("REDE", "Rede (Ethernet)"),
        ("WIFI", "Wi-Fi"),
        ("USB_REDE", "USB + Rede"),
        ("PARALELA", "Paralela"),
        ("OUTRA", "Outra"),
    ]

    STATUS_CHOICES = [
        ("ATIVA", "Ativa"),
        ("MANUTENCAO", "Em Manutenção"),
        ("DESATIVADA", "Desativada"),
        ("AGUARDANDO", "Aguardando Peças"),
    ]

    nome = models.CharField("Nome", max_length=100)
    ip = models.GenericIPAddressField("Endereço IP", protocol="both", blank=True, null=True)
    modelo = models.CharField("Modelo", max_length=100)
    fabricante = models.ForeignKey(
        Fabricante, on_delete=models.PROTECT, verbose_name="Fabricante"
    )
    numero_serie = models.CharField("Número de Série", max_length=100, blank=True)
    tipo = models.CharField("Tipo", max_length=20, choices=TIPO_CHOICES, default="LASER")
    conexao = models.CharField("Conexão", max_length=20, choices=CONEXAO_CHOICES, default="USB")
    localizacao = models.ForeignKey(
        Localizacao, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Localização"
    )
    departamento = models.CharField("Departamento", max_length=100, blank=True)
    responsavel = models.CharField("Responsável", max_length=100, blank=True)
    data_aquisicao = models.DateField("Data de Aquisição", null=True, blank=True)
    data_garantia = models.DateField("Data Fim Garantia", null=True, blank=True)
    contador_paginas = models.PositiveIntegerField("Contador de Páginas", default=0)
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default="ATIVA")
    observacoes = models.TextField("Observações", blank=True)
    tags = models.CharField("Tags", max_length=255, blank=True,
                           help_text="Separadas por vírgula")
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Impressora"
        verbose_name_plural = "Impressoras"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome} ({self.modelo})"