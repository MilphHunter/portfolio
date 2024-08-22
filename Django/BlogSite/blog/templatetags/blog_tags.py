from django import template
from django.db.models import Count
from blog.models import Post
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.simple_tag  # Для того чтобы быть допустимой библиотекой тегов, в каждом содержащем
# шаблонные теги модуле должна быть определена переменная с именем register. Эта переменная является экземпляром класса
# template.Library, и она используется для регистрации шаблонных тегов и фильтров приложения
#
# В функцию был добавлен декоратор @register.simple_tag, чтобы зарегистрировать тег(функцию) как простой тег
# . Если есть потребность зарегистрировать ее под другим именем, то это можно сделать, указав атрибут
# name, например @register.simple_tag(name='my_tag').
# Что бы использовать эту шляну в base шаблоне нужно использовать {% load название файла(blog_tags.py) %} этот файл
# должен находится в папке на уровне с views.py и т.д.
def total_posts():
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_post.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]
    # В приведенном выше шаблонном теге с помощью функции annotate() формируется набор запросов QuerySet, чтобы
    # посчитать общее число комментариев к каждому посту. Функция агрегирования Count используется для сохранения
    # количества комментариев в вычисляемом поле total_comments по каждому объекту Post.
    # Набор запросов QuerySet упорядочивается по вычисляемому полю в убывающем порядке. Также предоставляется
    # опциональная переменная count, чтобы ограничивать общее число возвращаемых объектов.


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))
