# Generated by Django 4.1.7 on 2023-03-11 13:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nation', models.CharField(blank=True, max_length=20, null=True, verbose_name='国')),
                ('market', models.CharField(blank=True, max_length=20, null=True)),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('code', models.CharField(blank=True, max_length=5, null=True)),
                ('division', models.CharField(blank=True, max_length=20, null=True)),
                ('industry_code_1', models.CharField(blank=True, max_length=10, null=True)),
                ('industry_division_1', models.CharField(blank=True, max_length=10, null=True)),
                ('industry_code_2', models.CharField(blank=True, max_length=10, null=True)),
                ('industry_division_2', models.CharField(blank=True, max_length=20, null=True)),
                ('scale_code', models.CharField(blank=True, max_length=10, null=True)),
                ('scale_division', models.CharField(blank=True, max_length=10, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Trades',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('brand_code', models.CharField(blank=True, max_length=30, null=True)),
                ('Date', models.DateField(blank=True, null=True)),
                ('Open', models.FloatField(blank=True, null=True, verbose_name='始値')),
                ('Close', models.FloatField(blank=True, null=True, verbose_name='終値')),
                ('High', models.FloatField(blank=True, null=True, verbose_name='高値')),
                ('Low', models.FloatField(blank=True, null=True, verbose_name='安値')),
                ('Volume', models.FloatField(blank=True, null=True, verbose_name='出来高')),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapp.brand')),
            ],
        ),
    ]
