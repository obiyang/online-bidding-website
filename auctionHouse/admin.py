from django.contrib import admin
from .models import Auction, Category, Message, Rating, Payment, Shipping, Bid

class AuctionAdmin(admin.ModelAdmin):
    
    
    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.exclude = ('highest_bid', 'winner')
        else:
            self.exclude = ()
        return super(AuctionAdmin, self).get_form(request, obj, **kwargs)


admin.site.register(Auction, AuctionAdmin)
admin.site.register(Category)
admin.site.register(Message)
admin.site.register(Rating)
admin.site.register(Payment)
admin.site.register(Shipping)
admin.site.register(Bid)