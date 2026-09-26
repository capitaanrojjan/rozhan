from django.contrib import admin

from .models import * 
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','slug', 'description','is_active')
    list_filter = ('is_active',)
    search_fields = ('name','descriotion',)
    ordering = ('name',)
    readonly_fields = ('slug',)
    list_editable = ('is_active',)

@admin.register(product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('category','slug','price')
    list_editable = ('price',)
    fieldsets = (
        ('NAME',{
            'fields':('category','slug')
        }),
        ('PRICE',{
            'fields':('price',)
        }),
        
    )