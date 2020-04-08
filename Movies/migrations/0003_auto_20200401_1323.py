# Generated by Django 2.2.3 on 2020-04-01 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Movies', '0002_auto_20200228_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='movie_alias',
            field=models.CharField(max_length=100, verbose_name='电影别名'),
        ),
        migrations.AlterField(
            model_name='movie',
            name='movie_cover',
            field=models.ImageField(blank=True, null=True, upload_to='MovieCover/%Y%m%d', verbose_name='电影封面图片路径'),
        ),
        migrations.AlterField(
            model_name='movie',
            name='movie_intro',
            field=models.CharField(blank=True, max_length=512, null=True, verbose_name='剧情简介'),
        ),
    ]
