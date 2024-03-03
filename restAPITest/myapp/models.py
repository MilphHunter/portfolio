from django.db import models


class BaseModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Color(models.IntegerChoices):
    Green = 1, 'Green'
    BLUE = 2, 'Blue'
    WHITE = 3, 'White'


class Car(BaseModel):
    name = models.CharField(max_length=30)
    color = models.IntegerField(choices=Color.choices)
    max_speed = models.IntegerField()

    def __str__(self):
        return f'{self.name} - {self.get_color_display()} - {self.max_speed}'
