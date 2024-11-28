from django.shortcuts import redirect, render,get_object_or_404
from .models import Cart, Product, CartProduct,Currency,Wishlist, Order,OrderProduct,UserProfile, Address
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from django.views.decorators.http import require_POST
from .forms import OrderForm,AddressForm,UserProfileForm, UserForm
from django.db.models import Q

# Create your views here.

def change_currency(request):
    if request.method == 'POST' and request.is_ajax():
        currency_code = request.POST.get('currency')

        # Fetch the Currency object based on the currency code
        currency = get_object_or_404(Currency, code=currency_code)

        # Update session with selected currency and conversion rate
        request.session['currency'] = currency.code
        request.session['currency_name'] = currency.name
        request.session['currency_conversion_rate'] = str(currency.conversion_rate)

        # Return JSON response indicating success
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    
def get_cart(request):
    # Ensure the session key is created if not present
    if not request.session.session_key:
        request.session.save()  # Force save session to create a session key

    if request.user.is_authenticated:
        # For authenticated users
        cart, created = Cart.objects.get_or_create(user=request.user)
        print(f"Authenticated user cart: {cart}, Created: {created}")
    else:
        # For non-authenticated users
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_key)
        print(f"Session-based cart: {cart}, Created: {created}, Session Key: {session_key}")

    print(f"Cart items: {cart.cartproduct_set.all()}")
    return cart

def update_cart(request):
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            action = request.POST.get('action')
            quantity = int(request.POST.get('quantity', 1))

            print(f'Received data - Product ID: {product_id}, Action: {action}, Quantity: {quantity}')  # Debugging

            if not product_id or not action:
                print('Missing product_id or action')  # Debugging
                return JsonResponse({'error': 'Missing product_id or action'}, status=400)

            product = get_object_or_404(Product, id=product_id)
            cart = get_cart(request)

            if action == 'add':
                cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
                if not created:
                    cart_product.quantity += quantity
                else:
                    cart_product.quantity = quantity
                cart_product.save()
            elif action == 'remove':
                cart_product = CartProduct.objects.filter(cart=cart, product=product).first()
                if cart_product:
                    if cart_product.quantity > 1:
                        cart_product.quantity -= 1
                        cart_product.save()
                    else:
                        cart_product.delete()
            elif action == 'update':
                if quantity <= 0:
                    return JsonResponse({'error': 'Quantity must be greater than 0'}, status=400)
                cart_product, created = CartProduct.objects.get_or_create(cart=cart, product=product)
                cart_product.quantity = quantity
                cart_product.save()
            else:
                return JsonResponse({'error': 'Invalid action'}, status=400)

            cart_products = CartProduct.objects.filter(cart=cart)
            subtotal = sum(cp.quantity * float(cp.product.price) for cp in cart_products)
            print(f"Calculated subtotal: {subtotal}")  # Debugging

            cart_data = {
                'total_items': cart_products.count(),
                'cart_subtotal': float(subtotal),  # Ensure this is sent as a float
                'products': [{
                    'id': cp.product.id,
                    'name': cp.product.name,
                    'price': float(cp.product.price),  # Ensure this is a float
                    'image_url': cp.product.image.url,
                    'quantity': cp.quantity  # Include the quantity
                } for cp in cart_products]
            }

            print(f"Cart data to be returned: {cart_data}")  # Debugging
            return JsonResponse(cart_data)

        except Exception as e:
            print(f"Error occurred: {e}")  # Debugging
            return JsonResponse({'error': f'An error occurred: {e}'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def index(request):
    # Fetch products and initialize cart
    products = Product.objects.all()
    cart = get_cart(request)  # Initialize cart here

    # Get cart details
    cart_products = cart.cartproduct_set.all()
    cart_items = cart.count_unique_items()
    total = cart.get_total_price()

    selected_currency = request.session.get('currency', 'USD')

    # Adjust product prices based on selected currency
    for product in products:
        product.price = product.get_price(selected_currency)
    for cart_product in cart_products:
        cart_product.product.price = cart_product.product.get_price(selected_currency)

    # Debug: Print cart details
    print(f"Index View - Cart: {cart}, Cart Products: {cart_products}")

    # Calculate currency_total
    currency_total = sum(cart_product.product.price * cart_product.quantity for cart_product in cart_products)
    currency_total = round(currency_total, 2)

    context = {
        'currency_total':currency_total,
        'cart_products': cart_products,
        'products': products,
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
        'selected_currency': selected_currency,
    }
    return render(request, 'index-2.html', context)


def product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    currencies = Currency.objects.all()  # Get all available currencies
    selected_currency = request.session.get('currency', 'USD')  # Default to USD if not set in session

    product_price = product.get_price(selected_currency)
    cart_items = cart.count_unique_items()

    product_data = {
        'id': product.id,
        'name': product.name,
        'price': product_price,
        'description': product.description,
        'image_url': product.image.url,
        'cart_items': cart_items,
        # 'categories': [category.name for category in product.categories.all()],  # Example: Assuming you have categories
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(product_data)
    else:
        return render(request, 'product_details.html', {'product': product, 'product_data': product_data, 'cart_items': cart_items, 'currencies': currencies,'selected_currency': selected_currency,'product_price': product_price})
    

@require_POST
def toggle_wishlist(request):
    print("Request body:", request.body)  # Debugging

    try:
        data = json.loads(request.body)
        print("Parsed JSON data:", data)  # Debug: check parsed data
        
        product_id = data.get('product_id')
        print("Product ID:", product_id)  # Debug: check product ID

        product = get_object_or_404(Product, id=product_id)
        print("Product found:", product)  # Debug: check if product is found

        if request.user.is_authenticated:
            # For authenticated users
            wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        else:
            # For non-authenticated users
            session_key = request.session.session_key
            if not session_key:
                request.session.save()  # Force save session to create a session key
                session_key = request.session.session_key
            
            wishlist, created = Wishlist.objects.get_or_create(session_id=session_key, product=product)
        
        print("Wishlist entry:", wishlist)  # Debug: check the wishlist entry
        print("Created:", created)  # Debug: check if the entry was newly created

        if not created:
            wishlist.delete()
            added = False
        else:
            added = True

        return JsonResponse({'added': added})
    except json.JSONDecodeError:
        print("JSON Decode Error")  # Debug: handle JSON decode error
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print("Exception:", str(e))  # Debug: catch any other exceptions
        return JsonResponse({'error': 'An error occurred'}, status=500)
    
# @login_required
def wishlist_view(request):
    if request.user.is_authenticated:
        # For authenticated users, filter wishlist by user
        wishlist_items = Wishlist.objects.filter(user=request.user)
    else:
        # For non-authenticated users, filter wishlist by session key
        session_key = request.session.session_key
        if not session_key:
            request.session.save()  # Ensure the session key is created
            session_key = request.session.session_key
        
        wishlist_items = Wishlist.objects.filter(session_id=session_key)
    
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

   
@login_required
def checkout(request):
    user = request.user
    cart = Cart.objects.get(user=user)
    cart_products = CartProduct.objects.filter(cart=cart)
    total = cart.get_total_price()
    cart_items = cart.count_unique_items()
    
    # Initialize forms with None
    order_form = None
    address_form = None
    shipping_address = None

    if request.method == 'POST':
        order_form = OrderForm(request.POST)
        address_form = AddressForm(user, request.POST)

        if 'existing_address' in request.POST:
            address_id = request.POST['existing_address']
            if address_id:
                shipping_address = get_object_or_404(Address, id=address_id, user=user)
                address_form = AddressForm(instance=shipping_address, user=user, data=request.POST)
        else:
            shipping_address = None
        
        if address_form.is_valid() and order_form.is_valid():
            if not shipping_address:
                shipping_address = address_form.save(commit=False)
                shipping_address.user = user
                shipping_address.save()

            order = order_form.save(commit=False)
            order.user = user
            order.shipping_address = shipping_address
            order.total_price = total
            order.payment_status = 'paid'
            order.status = 'pending'
            order.save()

            for cart_product in cart_products:
                OrderProduct.objects.create(
                    order=order,
                    product=cart_product.product,
                    quantity=cart_product.quantity
                )

            cart.products.clear()

            return redirect('order_confirmation', order_id=order.id)
    else:
        order_form = OrderForm()
        address_form = AddressForm(user=user)

    context = {
        'order_form': order_form,
        'address_form': address_form,
        'total': total,
        'cart': cart,
        'cart_products': cart_products,
        'cart_items': cart_items,
    }

    return render(request, 'checkout.html', context)


@login_required
def user_profile(request):
    orders = Order.objects.filter(user=request.user)

    if request.user.is_superuser:
        return redirect('admin:index')

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('user_profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'additional_addresses': user_profile.additional_addresses or [],
        'orders': orders
    }
    return render(request, 'user_profile.html', context)


def cart(request):
    products = Product.objects.all()

    cart = get_cart(request)
    cart_products = CartProduct.objects.filter(cart=cart)
    return render(request, 'cart.html', {'cart': cart, 'cart_products': cart_products,'products':products,})

@login_required
def get_address_details(request):
    address_id = request.GET.get('address_id')
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    address_data = {
        'first_name': address.first_name,
        'last_name': address.last_name,
        'email': address.email,
        'address_line_1': address.address_line_1,
        'country': address.country.code,  # Ensure this is the country code
        'state': address.state,
        'city': address.city,
        'zipcode': address.zipcode,
        'phone': address.phone,
    }

    return JsonResponse(address_data)


def search(request):
  products = Product.objects.all()  # Fetch all products from the database
  cart = get_cart(request)
  cart_products = CartProduct.objects.filter(cart=cart)
  cart_items = cart.count_unique_items()
  total = cart.get_total_price()  # Calculate total price here
  searchlist = Product.objects.all().order_by('-price')
  query = request.GET.get('q')

  if query:
    searchlist = searchlist.filter(
      Q(name__icontains = query) |
      Q(description__icontains = query)   
    ).distinct()


  context = {   
    'searchlist' : searchlist,
    'query':query,
    'products': products,
    'cart': cart,
    'cart_products': cart_products,
    'cart_items' : cart_items,
    'total' : total,
  }


  return render(request,'search_result.html',context)


def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    return render(request, 'invoice/general-invoice.html', {'order': order, 'order_products': order_products})

@login_required
def past_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'past_orders.html', {'orders': orders})

@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_tracking.html', {'order': order})