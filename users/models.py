from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
class profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL , on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length = 300 ,)
    class Role(models.TextChoices):
        CUSTOMER = "customer",_("customer")
        SELLER = "Seller" , _("Seller")
        STAFF = "Staff", _("Staff")
    role = models.CharField(max_length=12 , choices=Role.choices,default=Role.CUSTOMER)
    location = models.CharField(max_length=200 , blank=True , null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updeted_at= models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name ='پروفایل'
        verbose_name_plural='پروفایل ها'
        ordering = ('-created_at',)

    def __str__(self):
        return self.full_name
    
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def manage_profile(sender , instance , created , **kwarge):
    full_name = f'{instance.first_name} {instance.last_name}'.strip()
    if created:
        profile.abjects.create(user=instance , full_name=full_name)
    else:
       profile.objects.update_or_create(user=instance , defaults={'full_name':full_name})

