from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.db import models
from django.db.models import Avg, Count
from .forms import RegisterForm, ReviewForm
from .models import Product, Category, CartItem, Order, OrderItem, Wishlist
import razorpay
from django.conf import settings



client = razorpay.Client(
    auth=(
        settings.RAZORPAY_KEY_ID,
        settings.RAZORPAY_KEY_SECRET
    )
)

def home(request):
    search = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '').strip()

    products = Product.objects.filter(
        is_available=True
    )

    if search:
        products = products.filter(
            models.Q(name__icontains=search) |
            models.Q(description__icontains=search)
        )

    if category_id:
        products = products.filter(
            category_id=category_id
        )

    products = products.order_by('-created_at')

    categories = Category.objects.all()

    return render(
        request,
        'home.html',
        {
            'products': products,
            'categories': categories,
            'search': search,
        }
    )


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')

    else:
        form = RegisterForm()

    return render(
        request,
        'register.html',
        {'form': form}
    )


def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(
            request,
            'login.html',
            {
                'error': 'Invalid email or password.'
            }
        )

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('register')

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('home')


def cart(request):
    if not request.user.is_authenticated:
        return redirect('register')

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('product')

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    return render(
        request,
        'cart.html',
        {
            'cart_items': cart_items,
            'total': total,
        }
    )


def increase_quantity(request, item_id):
    if not request.user.is_authenticated:
        return redirect('register')

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    cart_item.quantity += 1
    cart_item.save()

    return redirect('cart')


def decrease_quantity(request, item_id):
    if not request.user.is_authenticated:
        return redirect('register')

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()

    return redirect('cart')


def remove_from_cart(request, item_id):
    if not request.user.is_authenticated:
        return redirect('register')

    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        user=request.user
    )

    cart_item.delete()

    return redirect('cart')


def checkout(request):
    if not request.user.is_authenticated:
        return redirect('register')

    cart_items = CartItem.objects.filter(
        user=request.user
    ).select_related('product')

    total = sum(
        item.product.price * item.quantity
        for item in cart_items
    )

    # Create Razorpay order
    razorpay_order = None

    if cart_items.exists():
        amount_paise = int(total * 100)

        razorpay_order = client.order.create(
            data={
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': 1
            }
        )

    if request.method == 'POST':

        address = request.POST.get('address')

        if not address:
            return render(
                request,
                'checkout.html',
                {
                    'cart_items': cart_items,
                    'total': total,
                    'error': 'Please enter your delivery address.',
                    'razorpay_order_id': razorpay_order['id'] if razorpay_order else '',
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                }
            )

        razorpay_payment_id = request.POST.get(
            'razorpay_payment_id'
        )

        razorpay_order_id = request.POST.get(
            'razorpay_order_id'
        )

        razorpay_signature = request.POST.get(
            'razorpay_signature'
        )

        # Check whether payment information was received
        if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
            return render(
                request,
                'checkout.html',
                {
                    'cart_items': cart_items,
                    'total': total,
                    'error': 'Payment was not completed.',
                    'razorpay_order_id': razorpay_order['id'] if razorpay_order else '',
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                }
            )

        # Verify Razorpay payment
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })

        except razorpay.errors.SignatureVerificationError:
            return render(
                request,
                'checkout.html',
                {
                    'cart_items': cart_items,
                    'total': total,
                    'error': 'Payment verification failed.',
                    'razorpay_order_id': razorpay_order['id'] if razorpay_order else '',
                    'razorpay_key': settings.RAZORPAY_KEY_ID,
                }
            )

        # Payment verified successfully
        order = Order.objects.create(
            user=request.user,
            total_amount=total,
            address=address,
            status='Paid'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Clear cart only after successful payment
        cart_items.delete()

        return redirect('home')

    return render(
        request,
        'checkout.html',
        {
            'cart_items': cart_items,
            'total': total,
            'razorpay_order_id': razorpay_order['id'] if razorpay_order else '',
            'razorpay_key': settings.RAZORPAY_KEY_ID,
        }
    )


def my_orders(request):
    if not request.user.is_authenticated:
        return redirect('register')

    orders = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items__product'
    ).order_by('-created_at')

    return render(
        request,
        'orders.html',
        {
            'orders': orders,
        }
    )

def product_detail(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    related_products = Product.objects.filter(
    category=product.category,
    is_available=True
    ).exclude(
    id=product.id
    )[:4]

    reviews = product.reviews.all().order_by('-created_at')

    average_rating = product.reviews.aggregate(
        average=Avg('rating')
    )['average']

    review_count = product.reviews.aggregate(
        count=Count('id')
    )['count']

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('register')

        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()

            return redirect(
                'product_detail',
                product_id=product.id
            )

    else:
        form = ReviewForm()

    return render(
        request,
        'product_detail.html',
        {
            'product': product,
            'reviews': reviews,
            'average_rating': average_rating,
            'review_count': review_count,
            'form': form,
            'related_products': related_products,
        }
    )
def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect('register')

    product = get_object_or_404(
        Product,
        id=product_id,
        is_available=True
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect('home')

def wishlist(request):
    if not request.user.is_authenticated:
        return redirect('register')

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').order_by('-added_at')

    return render(
        request,
        'wishlist.html',
        {
            'wishlist_items': wishlist_items,
        }
    )

def remove_from_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return redirect('register')

    wishlist_item = get_object_or_404(
        Wishlist,
        user=request.user,
        product_id=product_id
    )

    wishlist_item.delete()

    return redirect('wishlist')


def profile(request):
    if not request.user.is_authenticated:
        return redirect('register')

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.phone_number = request.POST.get('phone_number', '')

        if request.FILES.get('profile_image'):
            request.user.profile_image = request.FILES['profile_image']

        request.user.save()

        return redirect('profile')

    return render(
        request,
        'profile.html',
        {
            'user': request.user,
        }
    )