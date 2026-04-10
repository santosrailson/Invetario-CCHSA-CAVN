from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicoping',
            name='mac_address',
            field=models.CharField(blank=True, default='', max_length=17, verbose_name='MAC Address'),
        ),
        migrations.AddField(
            model_name='historicoping',
            name='fabricante_mac',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Fabricante (MAC)'),
        ),
        migrations.AlterField(
            model_name='historicoping',
            name='dispositivo_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='ID do Dispositivo'),
        ),
    ]
