# Generated by Django 3.2 on 2021-05-05 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volleyballschool', '0002_auto_20210503_2116'),
    ]

    operations = [
        migrations.CreateModel(
            name='OneTimeTraining',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.PositiveSmallIntegerField(verbose_name='Цена')),
            ],
            options={
                'verbose_name': 'Стоимость разового занятия',
                'verbose_name_plural': 'Стоимость разового занятия',
            },
        ),
        migrations.CreateModel(
            name='SubscriptionSamples',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='Наименование')),
                ('amount', models.PositiveIntegerField(verbose_name='Стоимость')),
                ('trainings_qty', models.PositiveSmallIntegerField(verbose_name='Количество тренировок')),
                ('validity', models.PositiveSmallIntegerField(verbose_name='Срок действия')),
                ('active', models.BooleanField(verbose_name='Активный')),
            ],
            options={
                'verbose_name': 'Абонемент',
                'verbose_name_plural': 'Абонементы',
            },
        ),
    ]