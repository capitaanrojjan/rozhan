from django.db import models
from django.utils import timezone

class Timestamp(models.Model):
    created_at = models.DateTimeField(auto_now_add=True , verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True , verbose_name='بروزرسانی')

class Meta:
    abstract = True

class BaseModel(Timestamp):
    is_active = models.BooleanField(default=True , verbose_name='فعال')

class Meta:
    abstract = True

class Author(models.Model):
    name = models.CharField(max_length=200 , verbose_name= 'نام نویسنده')
    def __str__(self):
        return self.name
    
class Book(models.Model):
    title = models.CharField(max_length=200 , verbose_name='عنوان کتاب')
    Author = models.ForeignKey(Author,on_delete=models.CASCADE, verbose_name='نویسنده')

    def __str__(self):
        return self.title
    
class Review(models.Model):
    Book = models.ForeignKey(Book,on_delete=models.CASCADE, verbose_name='کتاب')
    rating = models.IntegerField(verbose_name='امتیاز')
    comment = models.TextField(verbose_name='نظر')
    is_deleted = models.BooleanField(default=False , verbose_name='حذف شده')
def __str__(self):
    return f'Review for{self.Book.title}by{self.reting}stars'

def delete(self):
    self.is_deleted = True
    self.save()

class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug =models.SlugField(max_length=150,unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Meta:
    ordering = ['-name']
    def __str__(self):
        return self.name
    
class product(models.Model):
    category = models.ForeignKey(Category,on_delete=models.PROTECT,related_name='product')
    slug =  models.SlugField(max_length=150 , unique=True)
    price = models.PositiveIntegerField()

class Meta:
    ordering = ['price']

    def __str__(self):
       return str(self.price)