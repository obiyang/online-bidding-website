from django.views import generic
from django.views.generic.edit import CreateView
from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Avg
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render, redirect
from .models import Payment, Auction
from django.shortcuts import render, get_object_or_404
from .models import Auction, Payment, Shipping
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseForbidden
from .models import Auction
import openai
import mysql.connector
from django.shortcuts import render
from django.http import JsonResponse
from django.db import IntegrityError, transaction
import re
from .models import Auction, User, Message, Rating, Bid, Category
from datetime import datetime
import requests
from django.shortcuts import get_object_or_404, render
from .models import Auction, Payment, Shipping 
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


class HomeView(generic.TemplateView):
    template_name = 'home.html'

class CustomUserCreationForm(UserCreationForm):
    

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def user_profile(request, username=None):
    if username:
        user_profile = get_object_or_404(User, username=username)
        
    else:
        user_profile = request.user
    ratings = Rating.objects.filter(rated_user=user_profile).aggregate(average_rating=Avg('rating'))
    average_rating = ratings.get('average_rating') or "No ratings yet"

    auctions_won = Auction.objects.filter(winner=user_profile, status='Completed')
    auctions_sold = Auction.objects.filter(seller=user_profile, status='Completed')
    user_bids = Bid.objects.filter(user=user_profile).select_related('auction').order_by('-time')

    return render(request, 'user_profile.html', 
                  {
                      'profile_user': user_profile, 
                      'average_rating' : average_rating,
                      'auctions_won': auctions_won,
                      'auctions_sold': auctions_sold,
                      'user_bids': user_bids
                   }
                  )

def auctions_by_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    auctions = Auction.objects.filter(categories=category)
    categories = Category.objects.all()
    return render(request, 'auctions_by_category.html', {'auctions': auctions, 'category': category, 'categories': categories})

class AuctionListView(generic.ListView):
    template_name = 'auctionHouse/auction_list.html'
    queryset = Auction.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

#For creating a new auction
class AuctionForm(forms.ModelForm):

    number_of_days = forms.ChoiceField(
        choices=[(i, f"{i} days") for i in range(1, 11)],  
        label="Auction Duration"
    )
    class Meta:
        model = Auction
        fields = ['name', 'description', 'image', 'categories', 'reserve_price', 'number_of_days']
    def __init__(self, *args, **kwargs):
        super(AuctionForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

class AuctionCreateView(LoginRequiredMixin, CreateView):
    model = Auction
    form_class = AuctionForm
    template_name = 'auctionHouse/auction_create.html'
    success_url = reverse_lazy('auction') 

    def form_valid(self, form):
        # Calculate the end_time
        number_of_days = int(form.cleaned_data['number_of_days'])
        form.instance.end_time = datetime.now() + timedelta(hours=number_of_days*24)

        # Set the seller to the current user
        form.instance.seller = self.request.user 

        return super().form_valid(form)

#For placing bid
class BidForm(forms.Form):
    bid_amount = forms.DecimalField(max_digits=8, decimal_places=2)

class AuctionDetailView(generic.DetailView):
    template_name = 'auctionHouse/auction_detail.html'
    queryset = Auction.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        auction = self.get_object()

        auction.check_status()

        context['bid_form'] = BidForm() if self.object.status == 'Active' else None

        if auction.status == 'Completed':
            context['winner'] = auction.winner
            if self.request.user.is_authenticated and auction.winner:
                user_has_rated = auction.ratings.filter(rated_by=self.request.user).exists()
                is_eligible_to_rate = self.request.user in [auction.seller, auction.winner]
                context['show_rating_form'] = not user_has_rated and is_eligible_to_rate
                if context['show_rating_form']:
                    context['rating_form'] = RatingForm()
            else:
                context['show_rating_form'] = False
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to place a bid.")
            return HttpResponseRedirect(reverse('login'))
        
        auction = self.get_object()

        if auction.status != 'Active':
            messages.error(request, 'Bidding is not allowed at this time!')
            return redirect('auction_detail', pk=auction.pk)
        
        form = BidForm(request.POST)
        if form.is_valid():
            bid_amount = form.cleaned_data['bid_amount']

            if auction.highest_bid is None or bid_amount > auction.highest_bid:
                auction.highest_bid = bid_amount
                auction.winner = request.user
                auction.save()
                new_bid = Bid(auction=auction, user=request.user, amount=bid_amount)
                new_bid.save()
                messages.success(request, 'Your bid was successful!')
            else:
                messages.error(request, 'Your bid must be higher than the current highest bid.')

        return redirect('auction_detail', pk=auction.pk)



class MessageForm(forms.ModelForm):
    RECEIVER_CHOICES = [
        ('seller', 'Seller'),
        ('admin', 'Admin'),
        ('winner', 'winner')
    ]
    
    receiver_choice = forms.ChoiceField(choices=RECEIVER_CHOICES, label="Send To")

    class Meta:
        model = Message
        fields = ['receiver_choice','content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

@login_required
def send_message(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = auction.seller
            message.auction = auction
            receiver_choice = form.cleaned_data['receiver_choice']
            if receiver_choice == 'seller':
                message.receiver = auction.seller
            elif receiver_choice == 'admin':
                message.receiver = User.objects.filter(is_superuser=True).first()
            elif receiver_choice == 'winner' and auction.winner:
                message.receiver = auction.winner

            message.save()
            return redirect('view_messages')  
    else:
        form = MessageForm()

    return render(request, 'send_message.html', {'form': form, 'auction': auction})

@login_required
def view_messages(request):
    admin_users = User.objects.filter(is_superuser=True)
    received_messages = request.user.received_messages.all()
    received_from_admin = received_messages.filter(sender__in=admin_users)
    received_from_others = received_messages.exclude(sender__in=admin_users)

    sent_messages = request.user.sent_messages.all()

    return render(request, 'view_messages.html', {
        'received_from_admin': received_from_admin,
        'received_from_others': received_from_others,
        'sent_messages': sent_messages
    })

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['rating', 'comment']

@login_required
def submit_rating(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.auction = auction
            rating.rated_by = request.user

            if auction.winner == request.user:
                rating.rated_user = auction.seller
            else:
                rating.rated_user = auction.winner

            rating.save()
            
            return redirect('auction_detail', pk=auction_id)

   
    return redirect('auction_detail', pk=auction_id)


# 获取一个logger实例
logger = logging.getLogger(__name__)
def payment_view(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    payment, created = Payment.objects.get_or_create(
        auction=auction,
        defaults={'status': 'Pending', 'method': 'Credit/Debit Card'}
    )
    if payment.status == 'Completed':
        return render(request, 'payment_already_made.html', {'auction': auction})
    if request.method == 'POST' and payment.status != 'Completed':
        # 获取最高出价作为支付金额
        amount_to_pay = int(float(auction.highest_bid) * 100)

        # 构建向微服务发送的支付数据
        payment_data = {
            'amount': amount_to_pay,
            'currency': 'usd',  # 指定货币类型，例如 USD
        }
        # 微服务的 URL，替换为您的 NestJS 微服务 URL
        microservice_url = ''

        # 向微服务发送请求
        response = requests.post(microservice_url, json=payment_data)
        logger.info(f"Response from microservice: Status Code = {response.status_code}, Response Body = {response.text}")
        if response.status_code == 201:
            payment_response = response.json()
            # 您可能需要保存更多的支付信息到 Payment 模型
            payment.status = 'Completed'
            payment.stripe_payment_intent_id = payment_response['id']
            payment.save()
            Shipping.objects.create(auction=auction, shipping_status='Pending')
            return render(request, 'payment_success.html', {'auction': auction})
        else:
            # 处理支付错误
            error_message = response.json().get('message', 'Payment failed')
            return render(request, 'payment_error.html', {'message': error_message})

    return render(request, 'payment_form.html', {'auction': auction, 'payment': payment})

def shipping_view(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)
    shipping_info = Shipping.objects.filter(auction=auction).first()  # 获取相关联的运输信息

    return render(request, 'shipping_info.html', {'auction': auction, 'shipping_info': shipping_info})


def weekly_report_view(request):
    # 检查用户是否是管理员
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to view this report.")

    # 设置报告的时间范围，例如过去7天（一周）
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)

    # 获取在时间范围内创建的拍卖
    auctions_created = Auction.objects.filter(start_date__range=(start_date, end_date))
    total_created = auctions_created.count()
    total_amount_created = sum(auction.reserve_price for auction in auctions_created)

    # 获取在时间范围内完成的拍卖
    auctions_completed = auctions_created.filter(status='Completed')
    total_completed = auctions_completed.count()
    total_amount_completed = sum(auction.highest_bid for auction in auctions_completed if auction.highest_bid)

    context = {
        'total_created': total_created,
        'total_amount_created': total_amount_created,
        'total_completed': total_completed,
        'total_amount_completed': total_amount_completed,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'weekly_report.html', context)

def daily_report_view(request):
    # 检查用户是否是管理员
    if not request.user.is_superuser:
        return HttpResponseForbidden("You do not have permission to view this report.")

    # 获取当前时间
    now = timezone.now()
    # 设置当天的开始和结束时间
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)

    # 获取在当天创建的拍卖
    auctions_created = Auction.objects.filter(start_date__range=(start_date, end_date))
    total_created = auctions_created.count()
    total_amount_created = sum(auction.reserve_price for auction in auctions_created)

    # 获取在当天完成的拍卖
    auctions_completed = auctions_created.filter(status='Completed')
    total_completed = auctions_completed.count()
    total_amount_completed = sum(auction.highest_bid for auction in auctions_completed if auction.highest_bid)

    context = {
        'total_created': total_created,
        'total_amount_created': total_amount_created,
        'total_completed': total_completed,
        'total_amount_completed': total_amount_completed,
        'start_date': start_date,
        'end_date': end_date
    }

    return render(request, 'daily_report.html', context)

# Add your OpenAI API key
openai.api_key = ""

# Setting up database attributes
DB_CONFIG = {
    'host': "",
    'user': "",
    'password': "",
    'database': ""
}

# Function to execute SQL query
def execute_sql(query):
    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result


@login_required
def chatbot_view(request):
    # 检查用户是否是管理员
    if not request.user.is_superuser:
        # 如果不是管理员，显示 403 Forbidden 页面或重定向到其他页面
        return HttpResponseForbidden("Access denied. This page is for admin users only.")
        # 或者，重定向到其他页面，如：return redirect('home')

    if request.method == 'POST':
        user_input = request.POST.get('user_input')

        db_info = """Given the following SQL tables, your job is to Write a SQL query to {user_input}. You cannnot output anything except specific SQL query"
        CREATE TABLE `auctionHouse_auction` this table contains all the information about this auction(
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL, this is auction's name
  `description` longtext NOT NULL,
  `status` varchar(30) NOT NULL,
  `start_date` date NOT NULL,
  `end_time` datetime(6) NOT NULL,
  `reserve_price` decimal(8,2) NOT NULL,
  `highest_bid` decimal(8,2) DEFAULT NULL,
  `seller_id` int NOT NULL,
  `winner_id` int DEFAULT NULL,
  `image` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `auctionHouse_auction_seller_id` FOREIGN KEY (`seller_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_auction_winner_id` FOREIGN KEY (`winner_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_auction_categories` this table is used to match the auction with its categry(
  `id` bigint NOT NULL AUTO_INCREMENT,
  `auction_id` bigint NOT NULL,
  `category_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY  (`auction_id`,`category_id`),
  KEY `auctionHouse_auction_category_id` (`category_id`),
  CONSTRAINT `auctionHouse_auction_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_auction_category_id` FOREIGN KEY (`category_id`) REFERENCES `auctionHouse_category` (`id`)
) 
CREATE TABLE `auctionHouse_category` this table is used to find the category name according to category id(
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL, this is category's name
  PRIMARY KEY (`id`)
) 
CREATE TABLE `auctionHouse_bid` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(8,2) NOT NULL,
  `time` datetime(6) NOT NULL,
  `auction_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `auctionHouse_bid_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_bid_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_message` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `auction_id` bigint NOT NULL,
  `receiver_id` int NOT NULL,
  `sender_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_message_auction_id_de20b437_fk_auctionHo` (`auction_id`),
  KEY `auctionHouse_message_receiver_id_b65b3522_fk_auth_user_id` (`receiver_id`),
  KEY `auctionHouse_message_sender_id_357afddd_fk_auth_user_id` (`sender_id`),
  CONSTRAINT `auctionHouse_message_auction_id_de20b437_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_message_receiver_id_b65b3522_fk_auth_user_id` FOREIGN KEY (`receiver_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_message_sender_id_357afddd_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `method` varchar(20) NOT NULL,
  `status` varchar(10) NOT NULL,
  `auction_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_payment_auction_id_b0fe1d2d_fk_auctionHo` (`auction_id`),
  CONSTRAINT `auctionHouse_payment_auction_id_b0fe1d2d_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`)
) 
CREATE TABLE `auctionHouse_rating` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rating` int NOT NULL,
  `comment` longtext,
  `auction_id` bigint NOT NULL,
  `rated_by_id` int NOT NULL,
  `rated_user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_rating_auction_id` (`auction_id`),
  KEY `auctionHouse_rating_rated_by_id` (`rated_by_id`),
  KEY `auctionHouse_rating_rated_user_id` (`rated_user_id`),
  CONSTRAINT `auctionHouse_rating_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_rating_rated_by_id` FOREIGN KEY (`rated_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_rating_rated_user_id` FOREIGN KEY (`rated_user_id`) REFERENCES `auth_user` (`id`)
)
CREATE TABLE `auctionHouse_shipping` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `shipping_status` varchar(15) NOT NULL,
  `auction_id` bigint NOT NULL,
  `ups_tracking_number` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_shippin_auction_id_4092668a_fk_auctionHo` (`auction_id`),
  CONSTRAINT `auctionHouse_shippin_auction_id_4092668a_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`)
) 
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
)
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) 
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) 
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) 
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) 
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
)"""
        # 将数据库信息和用户输入组合
        combined_input = db_info + "\n\nUser asks: " + user_input

        # 向 GPT-4 发送请求
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": combined_input}]
        )
        ChatGPT_reply = response["choices"][0]["message"]["content"]

        # 检查是否是 SQL 查询
        # 使用正则表达式提取 SQL 语句
        match = re.search(r'```sql\s*(.*?)\s*```', ChatGPT_reply, re.DOTALL)
        if match:
            sql_query = match.group(1)
            try:
                with transaction.atomic():  # 使用 Django 的原子事务块
                    sql_result = execute_sql(sql_query)
                    response_data = {"reply": f"SQL Result: {sql_result}"}
            except Exception as e:
                return JsonResponse({"reply": f"Error executing SQL: {e}"})
        else:
            response_data = {"reply": "No SQL query detected"}
        
        return JsonResponse(response_data)

    return render(request, 'chat_bot4.html')

# 设置 OpenAI API 和数据库配置
openai.api_key = ""
SERVER_URL = ""
DB = ""
USER_NAME = ""
PASSWORD = ""

@login_required
def chat(request):
    # 检查用户是否是管理员
    if not request.user.is_superuser:
        if request.method == 'POST':
            user_input = request.POST.get('message')

        # 生成 SQL 查询
            sql_query = generate_sql(user_input)  # 调用 OpenAI API

        # 连接数据库并执行查询
            connection = mysql.connector.connect(host=SERVER_URL, user=USER_NAME, password=PASSWORD, database=DB)
            cursor = connection.cursor()
            cursor.execute(sql_query)
            results = cursor.fetchall()
            cursor.close()
            connection.close()

        # 格式化查询结果
            formatted_results = [row[0] for row in results]
            return JsonResponse({'query': sql_query, 'results': formatted_results})

        return render(request, 'chat.html')
    if request.method == 'POST':
        user_input = request.POST.get('message')

        # 生成 SQL 查询
        sql_query = generate_sql(user_input)  # 调用 OpenAI API

        # 连接数据库并执行查询
        connection = mysql.connector.connect(host=SERVER_URL, user=USER_NAME, password=PASSWORD, database=DB)
        cursor = connection.cursor()
        cursor.execute(sql_query)

        # 根据查询类型处理结果
        if sql_query.lower().startswith("select"):
            results = cursor.fetchall()
            # 格式化查询结果
            formatted_results = [row[0] for row in results]
            response_data = {'query': sql_query, 'results': formatted_results}
        else:
            connection.commit()  # 提交事务
            affected_rows = cursor.rowcount
            response_data = {'query': sql_query, 'affected_rows': affected_rows}

        cursor.close()
        connection.close()

        return JsonResponse(response_data)
    
    # 处理 GET 请求，返回一个页面或适当的响应
    return render(request, 'chat.html')  # 假设 'chat.html' 是您的模板

# 使用 OpenAI API 生成 SQL 查询的函数
def generate_sql(user_input):
    model_engine = "text-davinci-002"
    prompt = (
        f"Given the following SQL tables, your job is to write queries given a user’s request."
        '''
        CREATE TABLE `auctionHouse_auction` this table contains all the information about this auction(
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL, this is auction's name
  `description` longtext NOT NULL,
  `status` varchar(30) NOT NULL,
  `start_date` date NOT NULL,
  `end_time` datetime(6) NOT NULL,
  `reserve_price` decimal(8,2) NOT NULL,
  `highest_bid` decimal(8,2) DEFAULT NULL,
  `seller_id` int NOT NULL,
  `winner_id` int DEFAULT NULL,
  `image` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `auctionHouse_auction_seller_id` FOREIGN KEY (`seller_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_auction_winner_id` FOREIGN KEY (`winner_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_auction_categories` this table is used to match the auction with its categry(
  `id` bigint NOT NULL AUTO_INCREMENT,
  `auction_id` bigint NOT NULL,
  `category_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY  (`auction_id`,`category_id`),
  KEY `auctionHouse_auction_category_id` (`category_id`),
  CONSTRAINT `auctionHouse_auction_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_auction_category_id` FOREIGN KEY (`category_id`) REFERENCES `auctionHouse_category` (`id`)
) 
CREATE TABLE `auctionHouse_category` this table is used to find the category name according to category id(
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL, this is category's name
  PRIMARY KEY (`id`)
) 
CREATE TABLE `auctionHouse_bid` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(8,2) NOT NULL,
  `time` datetime(6) NOT NULL,
  `auction_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `auctionHouse_bid_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_bid_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_message` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `auction_id` bigint NOT NULL,
  `receiver_id` int NOT NULL,
  `sender_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_message_auction_id_de20b437_fk_auctionHo` (`auction_id`),
  KEY `auctionHouse_message_receiver_id_b65b3522_fk_auth_user_id` (`receiver_id`),
  KEY `auctionHouse_message_sender_id_357afddd_fk_auth_user_id` (`sender_id`),
  CONSTRAINT `auctionHouse_message_auction_id_de20b437_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_message_receiver_id_b65b3522_fk_auth_user_id` FOREIGN KEY (`receiver_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_message_sender_id_357afddd_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `method` varchar(20) NOT NULL,
  `status` varchar(10) NOT NULL,
  `auction_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_payment_auction_id_b0fe1d2d_fk_auctionHo` (`auction_id`),
  CONSTRAINT `auctionHouse_payment_auction_id_b0fe1d2d_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`)
) 
CREATE TABLE `auctionHouse_rating` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rating` int NOT NULL,
  `comment` longtext,
  `auction_id` bigint NOT NULL,
  `rated_by_id` int NOT NULL,
  `rated_user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_rating_auction_id` (`auction_id`),
  KEY `auctionHouse_rating_rated_by_id` (`rated_by_id`),
  KEY `auctionHouse_rating_rated_user_id` (`rated_user_id`),
  CONSTRAINT `auctionHouse_rating_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_rating_rated_by_id` FOREIGN KEY (`rated_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_rating_rated_user_id` FOREIGN KEY (`rated_user_id`) REFERENCES `auth_user` (`id`)
)
CREATE TABLE `auctionHouse_shipping` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `shipping_status` varchar(15) NOT NULL,
  `auction_id` bigint NOT NULL,
  `ups_tracking_number` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_shippin_auction_id_4092668a_fk_auctionHo` (`auction_id`),
  CONSTRAINT `auctionHouse_shippin_auction_id_4092668a_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`)
) 
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
)
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) 
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) 
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) 
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) 
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)'''
        f"{user_input}\n"
        f"SQL:"
    )
    response = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        temperature=0,
        max_tokens=150,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=["#", ";"]
    )
    return response.choices[0].text.strip()



